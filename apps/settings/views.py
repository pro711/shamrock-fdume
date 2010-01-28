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

from ragendja.dbutils import get_object_or_404
from ragendja.template import render_to_response


def choose_lang(request):
    return render_to_response(request, "settings/choose_lang.html")
