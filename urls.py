# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from ragendja.urlsauto import urlpatterns
from ragendja.auth.urls import urlpatterns as auth_patterns
from myapp.forms import UserRegistrationForm
from django.contrib import admin

admin.autodiscover()

handler500 = 'ragendja.views.server_error'

urlpatterns = auth_patterns + patterns('',
    ('^admin/(.*)', admin.site.root),
    (r'^$', 'django.views.generic.simple.direct_to_template',
        {'template': 'main.html'}),
    (r'^i18n/', include('django.conf.urls.i18n')),
    # Override the default registration form
    url(r'^account/register/$', 'registration.views.register',
        kwargs={'form_class': UserRegistrationForm},
        name='registration_register'),
    (r'^about/$', 'django.views.generic.simple.direct_to_template',
        {'template': 'about.html'}),
) + urlpatterns
