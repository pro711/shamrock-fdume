# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,Http404, HttpResponseForbidden,HttpResponse,HttpResponseNotFound, HttpResponseServerError
from django.core.paginator import Paginator, InvalidPage
from django.utils.encoding import force_unicode,smart_str
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, delete_object, \
    update_object
from django import forms as djangoforms

from google.appengine.ext import db
from google.appengine.ext.db import djangoforms as forms
from google.appengine.api import urlfetch
from mimetypes import guess_type
from myapp.forms import PersonForm
from myapp.models import Contract, File, Person
from apps.book.models import BookItem
from apps.lesson.models import Lesson, LessonComment, LessonCommentFetcher
from xml.dom import minidom
import datetime
import urlparse

from ragendja.dbutils import get_object_or_404
from ragendja.template import render_to_response

BBS_FETCH_ENTRANCE = 'http://bbs.fudan.edu.cn/bbs/0an?path=/groups/campus.faq/Lessons/kcjs'

class LessonAddForm(forms.ModelForm):
    description = djangoforms.CharField(widget=djangoforms.Textarea,required=False)
    tags = djangoforms.CharField()
    class Meta:
        model = Lesson          
        exclude = ['lesson_id', 'view_num', 'post_date', 'refreshed_time', ]

class LessonAddCommentForm(forms.ModelForm):
    class Meta:
        model = LessonComment          
        exclude = ['comment_id', 'commenter', 'lesson', 'post_date', 'from_bbs' ]


def lesson_index(request):
    q = Lesson.all()
    q.order("-post_date")
    results = q.fetch(8)
    num = len(results)
    items = [results[2*n:2*n+2] for n in range(num/2)]
    if num < 8 and (num%2 == 1) :
        items.append([results[-1],])
    
    template_values = {
            'lessons' : items,
            }
    
    return render_to_response(request, "lesson/lesson_index.html", template_values)

def lesson_all(request):
    q = Lesson.all()
    q.order("-post_date")
    # Paginate using django's pagination tools
    paginator = Paginator(q, 10)
    page = request.GET.get('page', 1)
    page_number = int(page)
    try:
        page_obj = paginator.page(page_number)
    except InvalidPage:
        raise Http404
    
    template_values = {
        'object_list': page_obj.object_list,
        'paginator': paginator,
        'page_obj': page_obj,

        'is_paginated': page_obj.has_other_pages(),
        'results_per_page': paginator.per_page,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'page': page_obj.number,
        'next': page_obj.next_page_number(),
        'previous': page_obj.previous_page_number(),
        'first_on_page': page_obj.start_index(),
        'last_on_page': page_obj.end_index(),
        'pages': paginator.num_pages,
        'hits': paginator.count,
        'page_range': paginator.page_range,
    }
    
    return render_to_response(request, "lesson/lesson_all.html", template_values)

def lesson_list(request):
    pass

@login_required
def lesson_add(request):
    if request.method == 'GET':
        form = LessonAddForm()
        template_values = {
                'form' : form,
                }
        return render_to_response(request, "lesson/lesson_add.html", template_values)
    else:
        form = LessonAddForm(request.POST)
        
        if form.is_valid():
            entity = form.save(commit=False)
            
            # Auto-increment lesson_id, starting from 1000
            q = Lesson.all()
            q.order("-lesson_id")
            results = q.fetch(1)
            if len(results) == 0:
                last_id = 1000
            else:
                last_id = results[0].lesson_id
            entity.lesson_id = last_id + 1
            
            # Deal with tags
            tagstrings=form.cleaned_data['tags'].strip().split(' ')
            entity.tags=tagstrings
            
            entity.put()
            
            # Automatically add comments from datastore
            entity.add_comment_fdubbs()
            
            return HttpResponseRedirect("/lesson/")
        else:
            template_values = {
                    'form' : form,
                    }
            return render_to_response(request, "lesson/lesson_add.html", template_values)

@login_required
def lesson_addcomment(request, lesson_id):
    if request.method == 'GET':
        form = LessonAddCommentForm()
        template_values = {
                'form' : form,
                }
        return render_to_response(request, "lesson/lesson_addcomment.html", template_values)
    else:
        form = LessonAddCommentForm(request.POST)
        
        if form.is_valid():
            if request.user.is_authenticated():
                entity = form.save(commit=False)
                
                # Auto-increment comment_id, starting from 1
                q = LessonComment.all()
                q.order("-comment_id")
                results = q.fetch(1)
                if len(results) == 0:
                    last_id = 0
                else:
                    last_id = results[0].comment_id
                entity.comment_id = last_id + 1
                
                # Set user
                entity.commenter = request.user
                # Set lesson
                lesson = get_object_or_404(Lesson, 'lesson_id =', long(lesson_id))
                entity.lesson = lesson
                
                entity.put()
                return HttpResponseRedirect(lesson.get_absolute_url())
            else:
                # not authenticated
                return HttpResponseRedirect("/lesson/")
        else:
            template_values = {
                    'form' : form,
                    }
            return render_to_response(request, "lesson/lesson_add.html", template_values)




def lesson_detail(request, lesson_id):
    """Lesson detail page."""
    q = Lesson.all()
    q.filter("lesson_id =", long(lesson_id))
    results = q.fetch(1)
    
    if len(results) == 0:
        raise Http404, "Lesson of id %s not found." % lesson_id
    else:
        lesson = results[0]
        comments = lesson.lessoncomment_set.fetch(10)
        template_values = {
                'e' : lesson,
                'comments' : comments,
                }
        # increment view_num
        lesson.view_num = lesson.view_num + 1
        lesson.put()
        
        return render_to_response(request, "lesson/lesson_detail.html", template_values)



def lesson_fetchbbs(request):
    """
    Fetch lesson comments from FDUBBS.
    Iteration of this function performs a traverse of bbs pages starting
    from the path defined in BBS_FETCH_ENTRANCE.
    """
    if request.method == 'GET':
        path = request.GET.get('path', '')
        if len(path) == 0:
            from_db = True  # whether path is from datastore or specified by user
            # Get one from datastore
            q = LessonCommentFetcher.all()
            q.filter('processed =', False)
            #~ q.filter('type =', 'd')
            #~ q.order("-timestamp")
            results = q.fetch(1)
            if len(results) == 0:
                return HttpResponse("Nothing to process in datastore.")
            else:
                item = results[0]
                path = item.path
        else:
            from_db = False

        #~ try:
        childs = []
        # fetch xml
        page = urlfetch.fetch(path)
        # parse xml
        content = page.content
        # a small hack to deal with gb2312 encoding problem
        # the xml is actually gbk encoded
        content = content.decode('gbk', 'ignore').encode('utf-8')
        content = content.replace('encoding="gb2312"', 'encoding="utf-8"')
        dom = minidom.parseString(content)
        # get parent type
        if len(dom.getElementsByTagName('bbs0an')) > 0:
            typ = 'd'
        else:
            typ = 'f'

        
        if typ == 'd':
            # process a directory
            ent = dom.getElementsByTagName('ent')
            for e in ent:
                t = e.attributes['t'].value
                rawtime = e.attributes['time'].value
                relpath = e.attributes['path'].value   #relative path
                title = e.firstChild.data
                try:
                    id = e.attributes['id'].value
                except KeyError, ex:
                    id = ''
                # process values
                post_date = datetime.datetime.strptime(rawtime, '%Y-%m-%dT%H:%M:%S')
                # determine the url of directory / file
                if t==u'f':  # is a file rather than a directory
                    childpath = path.replace('bbs/0an', 'bbs/anc') + relpath
                else:
                    childpath = path + relpath
                #~ childpath = urlparse.urljoin(path, relpath)
                #~ childpath = path[:path.rindex('/')]+relpath
                
                childs.append(childpath)
                # put entity in datastore
                childitem = LessonCommentFetcher(type=t, path=childpath, owner=id, post_date=post_date,
                    title=title, processed=False)
                childitem.put()
        elif typ == 'f':
            # process a file
            try:
                text = dom.getElementsByTagName('bbsanc')[0].firstChild.data
            except:
                text = 'ERROR'
            item.content = text
            item.put()
            childs.append(text)
            
        # mark parent item as processed
        if from_db:
            item.processed = True
            item.put()
        return HttpResponse('<html>Path:%s<br/>Item fetched:<br/> %s <br/>%s</html>' % (path,'<br/>'.join(childs),typ))
        #~ except:
            #~ raise HttpResponseServerError
        
                
            
    else:
        raise Http404
    

def refresh_lessons(request):
    """Refresh comments of lessons repeatly by cron"""
    q=Lesson.all().order("refreshed_time")
    results = q.fetch(5)
    [t.add_comment_fdubbs() for t in results]
    return HttpResponse('Refresh OK')
