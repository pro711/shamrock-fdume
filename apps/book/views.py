# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect,Http404, HttpResponseForbidden,HttpResponse,HttpResponseNotFound
from django.core.paginator import Paginator, InvalidPage
from django.utils.translation import ugettext_lazy as _
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
from apps.lesson.models import Lesson
#~ from douban import service as dbservice
import douban.service
# Please use your own api key instead. e.g. :
#APIKEY = "23eeeb4347bdd26bfc6b7ee9a3b755dd"
APIKEY = ''
SECRET = ''


from ragendja.dbutils import get_object_or_404
from ragendja.template import render_to_response

class BookAddForm(forms.ModelForm):
    description = djangoforms.CharField(widget=djangoforms.Textarea,required=False)
    class Meta:
        model = BookItem          
        exclude = ['book_id', 'post_date', 'owner','sold']
        
class BookAddDoubanForm(djangoforms.Form):
    search_text = djangoforms.CharField(required=False, max_length=100)
    
    



def book_index(request):
    q = BookItem.all()
    q.order("-post_date")
    results = q.fetch(8)
    #FIXED: odd numbers fetched
    num = len(results)
    items = [results[2*n:2*n+2] for n in range(num/2)]
    if num < 8 and (num%2 == 1) :
        items.append([results[-1],])
    
    template_values = {
            'books' : items,
            }
    
    return render_to_response(request, "book/book_index.html", template_values)

@login_required
def book_add(request):
    if request.method == 'GET':
        form = BookAddForm()
        template_values = {
                'form' : form,
                }
        return render_to_response(request, "book/book_add.html", template_values)
    else:
        form = BookAddForm(request.POST)
        
        if form.is_valid():
            if request.user.is_authenticated():
                entity = form.save(commit=False)
                # Set user
                entity.owner = request.user
                # Set valid_date
                
                # Auto-increment book_id, starting from 1000
                q = BookItem.all()
                q.order("-book_id")
                results = q.fetch(1)
                if len(results) == 0:
                    last_id = 1000
                else:
                    last_id = results[0].book_id
                entity.book_id = last_id + 1
                
                entity.put()
                return HttpResponseRedirect("/book/")
            else:
                # not authenticated
                return HttpResponseRedirect(reverse('apps.book.views.book_error', kwargs={'error_id':'1'}))
        else:
            template_values = {
                    'form' : form,
                    }
            return render_to_response(request, "book/book_add.html", template_values)


def book_detail(request, book_id):
    q = BookItem.all()
    q.filter("book_id =", long(book_id))
    results = q.fetch(1)
    
    if len(results) == 0:
        raise Http404, "Book of id %s not found." % book_id
    else:
        template_values = {
                'e' : results[0],
                'authenticated' : ((results[0].owner == request.user) and (results[0].sold == False))
                }
        return render_to_response(request, "book/book_detail.html", template_values)

def book_all(request):
    q = BookItem.all()
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
    
    return render_to_response(request, "book/book_all.html", template_values)

@login_required
def book_add_douban(request):
    if request.method == 'GET':
        form = BookAddDoubanForm()
        template_values = {
                'form' : form,
                'step' : 1,
                }
        return render_to_response(request, "book/book_add_douban.html", template_values)
    else:
        form = BookAddDoubanForm(request.POST)
        if form.is_valid():
            books = []
            search_text = form.cleaned_data['search_text']
            client = douban.service.DoubanService(api_key=APIKEY)
            feed = client.SearchBook(smart_str(search_text))
            for item in feed.entry:
                # FIXME: Needs improvement
                author  = ' '.join([author.name.text for author in item.author])
                try:
                    publisher = filter(lambda x:x.name=='publisher',item.attribute)[0].text
                except:
                    publisher = 'N/A'
                try:
                    price = filter(lambda x:x.name=='price',item.attribute)[0].text.replace('元','')
                except:
                    price ='0.00'
                #FIXME: If the url is unreadable, it shows strange things to you
                image_url = item.GetImageLink().href
                link = item.GetAlternateLink().href
                books.append({
                    'title' : item.title.text,
                    'author' : author,
                    'publisher' : publisher,
                    'price' : price,
                    #~ 'summary' : item.summary.text,
                    'image_url' : image_url,
                    'link' : link,
                    })
            template_values = {
                    'form' : form,
                    'step' : 2,
                    'books' : books,
                    }
            return render_to_response(request, "book/book_add_douban.html", template_values)
        else:
            template_values = {
                    'form' : form,
                    }
            return render_to_response(request, "book/book_add_douban.html", template_values)
            

def book_error(request, error_id):
    if error_id == '1':
        template_values = {
                'error_name' : _("Login required"),
                'detail' : _("You need to login to perform this operation."),
                }
    return render_to_response(request, "book/book_error.html", template_values)

def book_search(request):
    search_text=request.GET["search_text"]
    is_searching = True
    q=BookItem.all()
    q.order("-post_date")


    if len(search_text) != 0:
        message= _('Results for "%s"') % search_text
        results = filter(lambda x:search_text in x.title+x.author+x.publisher+
                    (x.tag if x.tag is not None else ''),q)
        
        if len(results) == 0:
            message = _("Sorry, no items matched")
    else:
        message = _("If you want to search for a book, type in something.")
        results = []
    
    # Paginate using django's pagination tools
    paginator = Paginator(results, 10)
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
        
        'message' : message,
    }

    return render_to_response(request, "book/book_search.html", template_values)

def book_mark_as_sold(request,book_id):
    q = BookItem.all()
    q.filter("book_id =", long(book_id))
    results = q.fetch(1)
    results[0].sold = True
    results[0].put()
    return HttpResponseRedirect("/book/%d/" %results[0].book_id)
