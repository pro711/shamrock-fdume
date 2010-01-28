# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('apps.book.views',
    (r'^$', 'book_index'),
    (r'^add/$', 'book_add'),
    (r'^add_from_douban/$', 'book_add_douban'),
    (r'^(?P<book_id>\d+)/$', 'book_detail'),
    (r'^error/(?P<error_id>\d+)/$', 'book_error'),
)
