import random

from google.appengine.ext import db

from gaegene.counter.models import GeneCounter, GeneCounterConfig
from gaegene.slug.models import slugify


class GeneTag(db.Model):
    name = db.StringProperty(required=False)
    count = db.IntegerProperty(required=False, default=0)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    
    def apply(self):
        GeneCounter.incr(self.counter_name)
    
    def remove(self):
        if self.live_count > 0:
            GeneCounter.decr(self.counter_name)
    
    def update_count(self):
        self.count = self.live_count
        self.put()
        return self.count
    
    @property
    def live_count(self):
        return GeneCounter.count(self.counter_name)
    
    @property
    def counter_name(self):
        return "GeneTagAppliedCount|%s" % self.key().name()
    
    @staticmethod
    def timeout(self):
        return GeneCounter.timeout(self.counter_name)
    
    @staticmethod
    def set_timeout(self, timeout):
        GeneCounter.set_timeout(self.counter_name)
    
    @staticmethod
    def max_shards(self):
        return GeneCounter.max_shards(self.counter_name)
    
    @staticmethod
    def add_shards(self, shards):
        GeneCounter.add_shards(self.counter_name, shards)
    
    @classmethod
    def key_name(cls, tagname):
        return "tag-%s" % tagname
    

class GeneTaggable(db.Model):
    tagnames = db.StringListProperty(default=[])
    
    def tag_append(self, tagname, clean=slugify, put=True):
        tagname_clean = clean(tagname)
        if tagname_clean and tagname_clean not in self.tagnames:
            self.tagnames.append(tagname_clean)
            if put:
                self.put()
    
    def tag_remove(self, tagname, clean=slugify, put=True):
        try:
            tagname_clean = clean(tagname)
            self.tagnames.remove(tagname_clean)
            if put:
                self.put()
        except:
            pass
    
    @property
    def tagnames_csv(self):
        return ", ".join(self.tagnames)
    
    def clear_tagnames(self, put=True):
        self.tagnames = []
        if put:
            self.put()
    
    def set_tagnames_list(self, tagnames, clean=slugify):
        self.clear_tagnames(put=False)
        for tagname in tagnames:
            self.tag_append(tagname, clean=clean, put=False)
        self.put()
    
    def set_tagnames_csv(self, tagnames_csv, clean=slugify):
        tagnames = []
        if tagnames_csv:
            tagnames = [
                clean(tagname.strip()) for tagname in tagnames_csv.split(",")
            ]
        self.set_tagnames_list(tagnames, clean=clean)
    
    @property
    def cloud(self):
        return Cloud(
            tagnames=self.tagnames, taggable_model=self.__class__
        )
    
    @classmethod
    def taggables(cls, tagname, clean=slugify):
        return cls.all().filter('tagnames =', clean(tagname))
    

class Cloud(object):
    def __init__(
            self,
            tagnames=[],
            taggable_model=GeneTaggable,
            taggable_filter=None,
            max_taggables=25,
            *args, **kwargs
        ):
        self._ranked_tags = None
        self.tagnames = list(tagnames)
        self.taggable_model = taggable_model
        self.taggable_filter = taggable_filter
        if self.taggable_filter is None:
            self.taggable_filter = lambda taggable: True
        self.max_taggables = max_taggables
        super(Cloud, self).__init__(*args, **kwargs)
    
    @property
    def ranked_tags(self):
        if self._ranked_tags is None:
            self._init_ranked_tags()
        return self._ranked_tags
    
    @property
    def min_rank(self):
        values = self.ranked_tags.values()
        return 0 if len(values) == 0 else min(values)
    
    @property
    def max_rank(self):
        values = self.ranked_tags.values()
        return 0 if len(values) == 0 else max(values)
    
    def _init_ranked_tags(self):
        self._ranked_tags = {}
        taggables = {}
        for tagname in list(self.tagnames):
            root_tag_taggables = dict(
                (taggable.key(), taggable) for
                taggable in self.taggable_model.taggables(tagname)
            )
            taggables.update(root_tag_taggables)
            if self.max_taggables and len(taggables) > self.max_taggables:
                break
        taggables = taggables.values()
        ranked_tags = self._ranked_tags
        for taggable in taggables:
            if self.taggable_filter(taggable):
                for tagname in taggable.tagnames:
                    ranked_tags[tagname] = ranked_tags.get(tagname, 0) + 1
    

