# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('apps.lesson.views',
    (r'^$', 'lesson_index'),
    (r'^add/$', 'lesson_add'),
    (r'^(?P<lesson_id>\d+)/$', 'lesson_detail'),
    (r'^(?P<lesson_id>\d+)/add_comment/$', 'lesson_addcomment'),
    (r'^fetchbbs/$', 'lesson_fetchbbs'),
    (r'^refresh/$', 'refresh_lessons'),
    (r'^refresh_seg/$', 'refresh_comment_seg'),
    (r'^all/$', 'lesson_all'),
)
