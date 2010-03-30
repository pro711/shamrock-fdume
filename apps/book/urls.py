# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('apps.book.views',
    (r'^$', 'book_index'),
    (r'^add/$', 'book_add'),
    (r'^add_from_douban/$', 'book_add_douban'),
    (r'^(?P<book_id>\d+)/$', 'book_detail'),
    (r'^(?P<book_id>\d+)/mark_as_sold/$', 'book_mark_as_sold'),
    (r'^error/(?P<error_id>\d+)/$', 'book_error'),
    (r'^item_search/$','book_search'),
    (r'^all/$', 'book_all'),
)
