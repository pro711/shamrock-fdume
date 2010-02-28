# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect,Http404, HttpResponseForbidden,HttpResponse,HttpResponseNotFound
from django.core.paginator import Paginator, InvalidPage
from django.utils.encoding import force_unicode,smart_str
from django.views.generic.list_detail import object_list, object_detail
from django.views.generic.create_update import create_object, delete_object, \
    update_object
from django import forms as djangoforms

from google.appengine.ext import db
from google.appengine.ext.db import djangoforms as forms
from mimetypes import guess_type
from myapp.forms import PersonForm
from myapp.models import Contract, File, Person
from apps.book.models import BookItem
from apps.lesson.models import Lesson, LessonComment

from ragendja.dbutils import get_object_or_404
from ragendja.template import render_to_response

class LessonAddForm(forms.ModelForm):
    description = djangoforms.CharField(widget=djangoforms.Textarea,required=False)
    tags = djangoforms.CharField()
    class Meta:
        model = Lesson          
        exclude = ['lesson_id', 'view_num', 'post_date', ]

class LessonAddCommentForm(forms.ModelForm):
    class Meta:
        model = LessonComment          
        exclude = ['comment_id', 'commenter', 'lesson', 'post_date', ]


def lesson_index(request):
    q = Lesson.all()
    q.order("-view_num")
    results = q.fetch(8)
    num = len(results)
    items = [results[2*n:2*n+2] for n in range(num/2)]
    if num < 8 and (num%2 == 1) :
        items.append([results[-1],])
    
    template_values = {
            'lessons' : items,
            }
    
    return render_to_response(request, "lesson/lesson_index.html", template_values)

def lesson_list(request):
    pass

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
            if request.user.is_authenticated():
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
                return HttpResponseRedirect("/lesson/")
            else:
                # not authenticated
                return HttpResponseRedirect("/lesson/")
        else:
            template_values = {
                    'form' : form,
                    }
            return render_to_response(request, "lesson/lesson_add.html", template_values)

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
