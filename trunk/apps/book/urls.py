# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('apps.book.views',
    (r'^$', 'book_index'),
    (r'^add/$', 'book_add'),
    (r'^(?P<book_id>\d+)/$', 'book_detail'),
#    (r'^create/$', 'add_person'),
#    (r'^show/(?P<key>.+)$', 'show_person'),

)
