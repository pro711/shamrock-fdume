# -*- coding: utf-8 -*-
from django.db.models import permalink, signals
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_unicode,smart_str
from google.appengine.ext import db
from django.contrib.auth.models import User

from ragendja.dbutils import cleanup_relations



class Lesson(db.Model):
    """Lesson information."""
    lesson_id = db.IntegerProperty(required=True, default=0)
    name = db.StringProperty(required=True)
    instructor = db.StringProperty(required=True)
    description = db.StringProperty(multiline=True)
    post_date = db.DateTimeProperty(auto_now=True)
    view_num = db.IntegerProperty(default=0)
    tags = db.ListProperty(str)

    def __unicode__(self):
        return '%s %s' % (self.instructor, self.name)

    @permalink
    def get_absolute_url(self):
        return ('apps.lesson.views.lesson_detail', (), {'lesson_id': smart_str(self.lesson_id)})


class LessonComment(db.Model):
    """Comment for a lesson."""
    comment_id = db.IntegerProperty(required=True, default=0)
    commenter = db.ReferenceProperty(User)
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    post_date = db.DateTimeProperty(auto_now=True)
    lesson = db.ReferenceProperty(Lesson)
