# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect,Http404, HttpResponseForbidden,HttpResponse,HttpResponseNotFound
from django.core.paginator import Paginator, InvalidPage
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


from ragendja.dbutils import get_object_or_404
from ragendja.template import render_to_response

class BookAddForm(forms.ModelForm):
    description = djangoforms.CharField(widget=djangoforms.Textarea,required=False)
    class Meta:
        model = BookItem          
        exclude = ['book_id', 'post_date', 'owner', ]




def book_index(request):
    q = BookItem.all()
    q.order("-post_date")
    results = q.fetch(8)
    #FIXME: odd numbers fetched
    num = len(results)
    items = [results[2*n:2*n+2] for n in range(num/2)]
    if num < 8 and (num%2 == 1) :
        items.append([results[-1],])
    
    template_values = {
            'books' : items,
            }
    
    return render_to_response(request, "book/book_index.html", template_values)

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
                return HttpResponseRedirect("/book/")
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
                }
        return render_to_response(request, "book/book_detail.html", template_values)









#~ def list_people(request):
    #~ return object_list(request, Person.all(), paginate_by=10)
#~ 
#~ def show_person(request, key):
    #~ return object_detail(request, Person.all(), key)
#~ 
#~ def add_person(request):
    #~ return create_object(request, form_class=PersonForm,
        #~ post_save_redirect=reverse('myapp.views.show_person',
                                   #~ kwargs=dict(key='%(key)s')))
#~ 
#~ def edit_person(request, key):
    #~ return update_object(request, object_id=key, form_class=PersonForm,
        #~ post_save_redirect=reverse('myapp.views.show_person',
                                   #~ kwargs=dict(key='%(key)s')))
#~ 
#~ def delete_person(request, key):
    #~ return delete_object(request, Person, object_id=key,
        #~ post_delete_redirect=reverse('myapp.views.list_people'))
#~ 
#~ def download_file(request, key, name):
    #~ file = get_object_or_404(File, key)
    #~ if file.name != name:
        #~ raise Http404('Could not find file with this name!')
    #~ return HttpResponse(file.file,
        #~ content_type=guess_type(file.name)[0] or 'application/octet-stream')
#~ 
#~ def create_admin_user(request):
    #~ user = User.get_by_key_name('admin')
    #~ if not user or user.username != 'admin' or not (user.is_active and
            #~ user.is_staff and user.is_superuser and
            #~ user.check_password('admin')):
        #~ user = User(key_name='admin', username='admin',
            #~ email='admin@localhost', first_name='Boss', last_name='Admin',
            #~ is_active=True, is_staff=True, is_superuser=True)
        #~ user.set_password('admin')
        #~ user.put()
    #~ return render_to_response(request, 'myapp/admin_created.html')
