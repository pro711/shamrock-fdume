# -*- coding: utf-8 -*-
from django.db.models import permalink, signals
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import force_unicode,smart_str
from google.appengine.ext import db
from django.contrib.auth.models import User
import re
import sys
from ragendja.dbutils import cleanup_relations
from smallseg.smallseg import SEG
seg = SEG()     # initialize word segmentation engine

class Lesson(db.Model):
    """Lesson information."""
    lesson_id = db.IntegerProperty(required=True, default=0)
    name = db.StringProperty(required=True)
    instructor = db.StringProperty(required=True)
    description = db.StringProperty(multiline=True)
    post_date = db.DateTimeProperty(auto_now_add=True)
    view_num = db.IntegerProperty(default=0)
    tags = db.ListProperty(str)
    refreshed_time = db.DateTimeProperty(auto_now=True)

    def __unicode__(self):
        return '%s %s %s' % (self.lesson_id, self.instructor, self.name)

    @permalink
    def get_absolute_url(self):
        return ('apps.lesson.views.lesson_detail', (), {'lesson_id': smart_str(self.lesson_id)})
        
    def add_comment_fdubbs(self):
        '''Find lesson comments in datastore with this lesson and add them.'''
        search_tags = [self.instructor, self.name] + self.tags
        search_tags = list(set(search_tags))    # remove duplicates
        search_tagslices = seg.cut(' '.join(search_tags).encode('utf-8'))
        #~ print >>  sys.stderr, ' '.join(search_tagslices)

        for stag in search_tagslices:
            q = LessonCommentFetcher.all()
            q.filter('processed =', True).filter('type =', 'f')
            q.filter('title_slices =', stag)
            
            for e in q:
                matched = 0
                title = e.title
                title_slices = e.title_slices   # split words
                #~ for i in title_slices:
                    #~ print >> sys.stderr,i,
                for t in search_tags:
                    for s in title_slices:
                        len_s = len(s)
                        if len_s>1 and s in t:      # single character is futile
                            matched = matched + len_s**2     # power weight
                            #~ break
                # if matches self.instructor, it's more likely we've found the right lesson
                if self.instructor in title:
                    matched = matched + 9
                #~ if matched > 10:    # FIXME: a simple threshold, needs a better algorithm
                # caculate threshold
                th1 = sum(map(lambda x:min(9,len(x)**2),search_tags)) / 2
                #~ print >>sys.stderr, th1, matched
                th2 = 12     #   2^2 + 3^2
                threshold = min(th1,th2)
                if matched > threshold:
                    # Put in datastore
                    # Auto-increment comment_id, starting from 1
                    qc = LessonComment.all()
                    qc.order("-comment_id")
                    results = qc.fetch(1)
                    if len(results) == 0:
                        last_id = 0
                    else:
                        last_id = results[0].comment_id
                    
                    qc = LessonComment.all()
                    results = qc.filter('lesson =', self).filter('title =', e.title)
                    if not len(results):
                        # process content, filter out useless markups
                        content=e.content
                        content = re.sub(r'>1b\[[\d;]*m','',content)
                        # put in datastore
                        comment = LessonComment(comment_id=last_id+1,title=e.title,content=content,
                                            lesson=self,from_bbs=True)
                        comment.put()


class LessonComment(db.Model):
    """Comment for a lesson."""
    comment_id = db.IntegerProperty(required=True, default=0)
    commenter = db.ReferenceProperty(User)
    title = db.StringProperty(required=True)
    content = db.TextProperty(required=True)
    post_date = db.DateTimeProperty(auto_now=True)
    lesson = db.ReferenceProperty(Lesson)
    from_bbs = db.BooleanProperty()
    
    def __unicode__(self):
        return '%s %s' % (self.comment_id, self.title)
    
    
class LessonCommentFetcher(db.Model):
    """
    Information used to guide fetching lesson comments from fdubbs.
    type       'd': directory; 'f': post file
    path        absolute path of post
    title       diretory or post title
    owner       poster
    post_date   date of post
    timestamp   timestamp
    processed   whether item is processed
    """
    type = db.StringProperty(required=True)
    path = db.StringProperty(required=True)
    title = db.StringProperty()
    content = db.TextProperty()
    owner = db.StringProperty(default=_("Anonymous"))
    post_date = db.DateTimeProperty()
    timestamp = db.DateTimeProperty(auto_now=True)
    processed = db.BooleanProperty(default=False)
    title_slices = db.ListProperty(str)

    def __unicode__(self):
        return '[%s] %s %s' % (self.type, self.timestamp, self.title)







