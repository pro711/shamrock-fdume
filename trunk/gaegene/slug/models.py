import re

from google.appengine.ext import db


def force_unicode(s, encoding='utf-8', strings_only=False, errors='strict'):
    """
    Similar to smart_unicode, except that lazy instances are resolved to
    strings, rather than kept as lazy objects.

    If strings_only is True, don't convert (some) non-string-like objects.
    
    Mostly lifted from django.utils.encoding.slugify().
    """
    if strings_only and isinstance(
        s, (
            types.NoneType,
            int,
            long,
            datetime.datetime,
            datetime.date,
            datetime.time,
            float
            )
        ):
        return s
    if not isinstance(s, basestring,):
        if hasattr(s, '__unicode__'):
            s = unicode(s)
        else:
            try:
                s = unicode(str(s), encoding, errors)
            except UnicodeEncodeError:
                if not isinstance(s, Exception):
                    raise
                # If we get to here, the caller has passed in an Exception
                # subclass populated with non-ASCII data without special
                # handling to display as a string. We need to handle this
                # without raising a further exception. We do an
                # approximation to what the Exception's standard str()
                # output should be.
                s = ' '.join([force_unicode(arg, encoding, strings_only,
                        errors) for arg in s])
    elif not isinstance(s, unicode):
        s = unicode(s, encoding, errors)
    return s

def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    
    Mostly lifted from django.template.defaultfilters.slugify().
    """
    import unicodedata
    value = unicodedata.normalize('NFKD', force_unicode(value)).encode(
        'ascii', 'ignore'
    )
    value = unicode(re.sub('[^\w\s-]', '', value).strip().lower())
    return re.sub('[-\s]+', '-', value)


class GeneSlugIndex(db.Model):
    """
    Serves as the root of a slug entity group.
    """
    @property
    def name(self):
        return self.key().name()
    
    def __unicode__(self):
        return self.name
    
    def get_slug(self, name):
        slug = None
        if name is not None:
            key_name = "slug-%s" % name
            slug = GeneSlug.get_by_key_name(key_name, parent=self)
        return slug
    
    def get_sluggable(self, name):
        sluggable = None
        slug = self.get_slug(name)
        if slug is not None:
            sluggable = slug.sluggable
        return sluggable
    
    def delete(self):
        slugs = GeneSlug.all().ancestor(self)
        for slug in slugs:
            self.free_slug(slug)
        super(GeneSlugIndex, self).delete()
    
    def free_slug(self, slug):
        if slug is not None:
            slug.delete()
    
    def free_slug_name(self, name):
        slug = self.get_slug(name)
        self.free_slug(slug)
    
    def reserve_slug(
            self, name, sluggable,
            reserved_slugs=[],
            previous_name=None,
            improvise=True
        ):
        existing_slug = None
        if name is not None:
            slug = None
            name = slugify(name)
            key_name = "slug-%s" % name
            if name == previous_name:
                existing_slug = GeneSlug.get_by_key_name(
                    key_name, parent=self
                )
                if existing_slug is not None:
                    return existing_slug
        
        def txn():
            # If we were given a previous name, free it
            if previous_name:
                self.free_slug_name(previous_name)
                existing_old_slug = GeneSlug.get_by_key_name(
                    previous_name, parent=self
                )
                if existing_old_slug is not None:
                    self.free_slug(existing_slug)
            slug = None
            # If we got a name, reserve it
            if name is not None:
                count = 1
                slug_name = name
                while True:
                    slug_key_name = "slug-%s" % slug_name
                    if slug_name in reserved_slugs:
                        slug = True
                    else:
                        slug = GeneSlug.get_by_key_name(
                            slug_key_name, parent=self
                        )
                    if slug:
                        if improvise:
                            # Calculate new slug name (e.g. name-1, name-2...)
                            slug_name = u'%s-%s' % (name, count)
                            count += 1
                        else:
                            msg = "That slug name is "
                            if slug == True:
                                msg += "reserved."
                            else:
                                msg += "already taken."
                            raise db.BadValueError, msg
                    else:
                        slug = GeneSlug(
                            key_name=slug_key_name,
                            parent=self,
                            name=slug_name,
                            sluggable=sluggable
                        )
                        slug.put()
                        break
            return slug
        
        return db.run_in_transaction(txn)
    
    def update_slug(self, slug, reserved_slugs=[], improvise=True):
        sluggable = slug.sluggable
        name = slug.key().name()
        # Is this an old style slug?
        if name[0:5] != 'slug-':
            new_slug = self.reserve_slug(
                name, sluggable,
                reserved_slugs=reserved_slugs,
                improvise=improvise
            )
        self.free_slug(slug)
    


class GeneSlug(db.Model):
    sluggable = db.ReferenceProperty(
        required=False, collection_name='slugs'
    )
    
    @property
    def name(self):
        name = self.key().name()
        if name[:5] == 'slug-':
            name = name[5:]
        return name
    
    @property
    def index(self):
        return self.parent()
    
    def __unicode__(self):
        return self.name
    


class GeneSluggable(db.Model):
    slug_entity = db.ReferenceProperty(
        GeneSlug, required=False, collection_name='sluggables'
    )
    slug_entity_name = db.StringProperty(required=False)
    
    def __init__(
            self,
            slug_name=None,
            slug_index_name=None,
            slug_index_parent=None,
            reserved_slugs=[],
            *args, **kwargs
        ):
        super(GeneSluggable, self).__init__(*args, **kwargs)
        if slug_name:
            self.put_with_slug(
                slug_name,
                slug_index_name=slug_index_name,
                slug_index_parent=slug_index_parent,
                reserved_slugs=reserved_slugs,
                improvise=True
            )
    
    @property
    def slug_name(self):
        if self.slug_entity_name is not None:
            return self.slug_entity_name
        elif self.slug_entity:
            return self.slug_entity.name
        return None
    
    @property
    def slug_index(self):
        if self.slug_entity:
            return self.slug_entity.index
        return None
    
    def put_with_slug(
            self, slug_name,
            slug_index_name=None,
            slug_index_parent=None,
            reserved_slugs=[],
            improvise=True
        ):
        if not self.is_saved():
            self.put()
        if self.slug_name and self.slug_name == slug_name:
            return slug_name
        if not slug_index_name:
            slug_index_name = self.kind()
        slug_index = self.get_or_insert_slug_index(
            name=slug_index_name, parent=slug_index_parent
        )
        self.slug_entity = slug_index.reserve_slug(
            slug_name, self,
            previous_name=self.slug_name,
            reserved_slugs=reserved_slugs,
            improvise=improvise
        )
        if self.slug_entity is not None:
            self.slug_entity_name = self.slug_entity.name
        self.put()
        return self.slug_name
    
    def delete(self):
        if self.slug_entity:
            self.slug_index.free_slug(self.slug_entity)
        super(GeneSluggable, self).delete()
    
    def update_old_slug(self, reserved_slugs=[]):
        if self.is_saved():
            slug_index_name=None
            slug_index_parent=None
            slug_entity = self.slug_entity
            if slug_entity is not None:
                slug_index = self.slug_index
                if slug_index is not None:
                    slug_index_name = slug_index.name
                    slug_index_parent = slug_index.parent()
                if not slug_index_name:
                    slug_index_name = self.kind()
                slug_index = self.get_or_insert_slug_index(
                    name=slug_index_name, parent=slug_index_parent
                )
                self.slug_entity = slug_index.reserve_slug(
                    self.slug_name, self,
                    previous_name=self.slug_name,
                    reserved_slugs=reserved_slugs
                )
                if self.slug_entity is not None:
                    self.slug_entity_name = self.slug_entity.name
                self.put()
        return self.slug_name
    
    @classmethod
    def get_or_insert_slug_index(cls, name=None, parent=None):
        if not name:
            name = cls.kind()
        if not parent:
            slug_index = GeneSlugIndex.get_or_insert(name)
        else:
            kwargs = {'parent' : parent}
            slug_index = GeneSlugIndex.get_or_insert(name, **kwargs)
        return slug_index
    
    @classmethod
    def get_by_slug(
            cls, slug_name,
            slug_index_name=None,
            slug_index_parent=None,
            max_tries=3
        ):
        sluggable = None
        slug_index = None
        tries = 0
        while tries < max_tries:
            tries = tries + 1
            try:
                if not slug_index_name:
                    slug_index_name = cls.kind()
                if slug_index is None:
                    slug_index = GeneSlugIndex.get_by_key_name(
                        slug_index_name, parent=slug_index_parent
                    )
                if slug_index is not None:
                    sluggable = slug_index.get_sluggable(slug_name)
                break
            except:
                if tries >= max_tries:
                    raise
        return sluggable

