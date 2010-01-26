# -*- coding: utf-8 -*-
from django.db.models import permalink, signals
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_unicode,smart_str
from google.appengine.ext import db
from django.contrib.auth.models import User

from ragendja.dbutils import cleanup_relations
from apps.lesson.models import Lesson




class BookItem(db.Model):
    """Book item to be transferred."""
    book_id = db.IntegerProperty(required=True, default=0)
    title = db.StringProperty(required=True)
    author = db.StringProperty(required=True)
    publisher = db.StringProperty(required=True)
    description = db.StringProperty(multiline=True)
    owner = db.ReferenceProperty(User)
    orig_price = db.FloatProperty()
    offer_price = db.FloatProperty(required=True)
    location = db.StringProperty()
    contact = db.StringProperty(required=True)
    post_date = db.DateTimeProperty(auto_now=True)
    valid_date = db.DateTimeProperty()
    tag = db.StringProperty()
    course = db.ReferenceProperty(Lesson)


    def __unicode__(self):
        return '%s %s' % (self.title, self.author)

    @permalink
    def get_absolute_url(self):
        return ('apps.book.views.book_detail', (), {'book_id': smart_str(self.book_id)})
