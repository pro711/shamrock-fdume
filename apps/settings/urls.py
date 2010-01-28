# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

urlpatterns = patterns('apps.settings.views',
    (r'^choose_lang/$', 'choose_lang'),

)
