# -*- coding: utf-8 -*-
from django.db.models import permalink, signals
from google.appengine.ext import db
from ragendja.dbutils import cleanup_relations

class User(db.Model):
    """User infomation."""
    uid = db.IntegerProperty(required=True)
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.StringProperty(required=True)
    
class Course(db.Model):
    """Course infomation."""
    course_id = db.IntegerProperty(required=True)

class BookItem(db.Model):
    """Book item to be transferred."""
    book_id = db.IntegerProperty(required=True)
    title = db.StringProperty(required=True)
    author = db.StringProperty(required=True)
    publisher = db.StringProperty(required=True)
    description = db.StringProperty()
    owner = db.ReferenceProperty(User,required=True)
    orig_price = db.FloatProperty()
    offer_price = db.FloatProperty(required=True)
    location = db.StringProperty()
    contact = db.StringProperty(required=True)
    post_date = db.DateTimeProperty()
    valid_date = db.DateTimeProperty()
    tag = db.StringProperty()
    course = db.ReferenceProperty(Course)


    def __unicode__(self):
        return '%s %s' % (self.title, self.author)

    @permalink
    def get_absolute_url(self):
        return ('apps.book.views.book_details', (), {'key': self.key(),
                                                        'id': self.book_id})
