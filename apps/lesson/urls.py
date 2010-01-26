# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('apps.lesson.views',
    (r'^$', 'lesson_index'),
    (r'^add/$', 'lesson_add'),
    (r'^(?P<lesson_id>\d+)/$', 'lesson_detail'),
    (r'^(?P<lesson_id>\d+)/add_comment/$', 'lesson_addcomment'),

)
