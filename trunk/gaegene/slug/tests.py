from google.appengine.ext import db

from django.test import TestCase

from gaegene.slug.models import GeneSluggable, GeneSlug, GeneSlugIndex


class GeneSlugTest(TestCase):
    def setUp(self):
        self.sluggable = GeneSluggable(slug_name=u'sluggable')
        self.sluggable2 = GeneSluggable()
        self.sluggable2.put()
        self.sluggable2.put_with_slug(u'sluggable2')
    
    def test_setup(self):
        self.assertEqual(self.sluggable.slug_name, 'sluggable')
        self.assertEqual(self.sluggable2.slug_name, 'sluggable2')
    
    def test_get_by_slug(self):
        slug_name = self.sluggable.slug_name
        lookup = GeneSluggable.get_by_slug(slug_name)
        self.failUnless(lookup)
        self.assertEqual(lookup.key(), self.sluggable.key())
        self.sluggable.delete()
        self.assertEqual(GeneSlug.all().count(), 1)
        lookup = GeneSluggable.get_by_slug(slug_name)
        self.failIf(lookup)
    
    def test_duplicate_slug(self):
        slug_name = self.sluggable.slug_name
        sluggable = GeneSluggable(slug_name=slug_name)
        self.assertEqual(sluggable.slug_name, '%s-1' % slug_name)
        sluggable = GeneSluggable()
        sluggable.put()
        sluggable.put_with_slug(slug_name)
        self.assertEqual(sluggable.slug_name, '%s-2' % slug_name)
        try:
            self.sluggable2.put_with_slug(slug_name, improvise=False)
            self.fail()
        except db.BadValueError:
            pass
    
    def test_numeric_slug(self):
        sluggable = GeneSluggable(slug_name='1234')
        self.failUnless(sluggable)
        self.assertEqual(sluggable.slug_name, '1234')
    
    def test_change_slug(self):
        self.sluggable.put_with_slug('SLUGGABLE')
        self.assertEqual(self.sluggable.slug_name, 'sluggable')
        self.sluggable.put_with_slug('NEW-SLUG')
        self.assertEqual(self.sluggable.slug_name, 'new-slug')
        self.sluggable.put_with_slug('NEW-SLUG')
        self.assertEqual(self.sluggable.slug_name, 'new-slug')
        self.sluggable.put_with_slug('new-slug')
        self.assertEqual(self.sluggable.slug_name, 'new-slug')
        self.sluggable.put_with_slug('new-slug')
        self.assertEqual(self.sluggable.slug_name, 'new-slug')
    
    def test_get_sluggable(self):
        slug_entity = self.sluggable.slug_entity
        self.failUnless(slug_entity)
        self.assertEqual(self.sluggable.key(), slug_entity.sluggable.key())
    
    def test_delete_index(self):
        self.sluggable.slug_index.delete()
        self.failIf(GeneSlug.all().count())
    
    def test_reserved_slugs(self):
        reserved_slugs = ['foo', 'goo']
        slug_name = reserved_slugs[0]
        sluggable = GeneSluggable(
            slug_name=slug_name, reserved_slugs=reserved_slugs
        )
        self.assertEqual(sluggable.slug_name, '%s-1' % slug_name)
        sluggable = GeneSluggable()
        sluggable.put()
        sluggable.put_with_slug(slug_name, reserved_slugs=reserved_slugs)
        self.assertEqual(sluggable.slug_name, '%s-2' % slug_name)
        try:
            self.sluggable2.put_with_slug(
                slug_name,
                reserved_slugs=reserved_slugs,
                improvise=False)
            self.fail()
        except db.BadValueError:
            pass
        slug_name = reserved_slugs[1]
        sluggable = GeneSluggable(
            slug_name=slug_name, reserved_slugs=reserved_slugs
        )
        self.assertEqual(sluggable.slug_name, '%s-1' % slug_name)
    
    def test_get_none_slug(self):
        lookup = GeneSluggable.get_by_slug(None)
        self.failIf(lookup)
        lookup = GeneSluggable.get_by_slug('')
        self.failIf(lookup)
    
    def test_set_none_slug(self):
        self.sluggable.put_with_slug(None)
        self.assertEqual(GeneSlug.all().count(), 1)
    
    def test_delete_slug(self):
        self.sluggable.delete()
        self.assertEqual(GeneSlug.all().count(), 1)
    


class GeneSlugLegacyTest(TestCase):
    def setUp(self):
        self.sluggable = GeneSluggable(slug_name=u'sluggable')
        self.sluggable2 = GeneSluggable()
        self.sluggable2.put()
        self.sluggable2.put_with_slug(u'sluggable2')
    
    def test_convert(self):
        self.sluggable.update_old_slug()
        slug_name = self.sluggable.slug_name
        slug_key_name = self.sluggable.slug_entity.key().name()
        self.assertEqual(slug_name, u'sluggable')
        self.assertEqual(slug_key_name, u'slug-sluggable')
        lookup = GeneSluggable.get_by_slug(slug_name)
        self.failUnless(lookup)
        self.assertEqual(lookup.key(), self.sluggable.key())
        self.assertEqual(GeneSlug.all().count(), 2)
        lookup_old = GeneSlug.get_by_key_name(slug_name)
        self.failIf(lookup_old)
    

class Person(GeneSluggable):
    """
    All Persons have the same slug_index and thus all person slug names are
    unique.
    """
    name = db.StringProperty()

class Dog(GeneSluggable):
    """
    Dogs use an index based on their owner and thus all dogs belonging
    to a single owner have unique slug names, but dogs with different owners
    can share the same slug name.
    """
    name = db.StringProperty()
    owner = db.ReferenceProperty(
        Person, required=False, collection_name='dogs'
    )
    
    @classmethod
    def get_by_slug_and_owner(cls, slug_name, owner):
        """
        A syntactic-sugar method for finding a dog by its slug and owner.
        """
        return cls.get_by_slug(slug_name, slug_index_parent=owner)
    
class Cat(GeneSluggable):
    """
    Cats use an index based on their owner and thus all cats belonging
    to a single owner have unique slug names, but cats with different owners
    can share the same slug name.
    """
    name = db.StringProperty()
    owner = db.ReferenceProperty(
        Person, required=False, collection_name='cats'
    )
    
    def __init__(self, slug_name=None, *args, **kwargs):
        super(Cat, self).__init__(*args, **kwargs)
        if not self.slug_name:
            if not slug_name:
                slug_name = kwargs.get('name', None)
            slug_index_parent = kwargs.get('owner', None)
            self.put_with_slug(
                slug_name,
                slug_index_parent=slug_index_parent
            )
    
    @classmethod
    def get_by_slug_and_owner(cls, slug_name, owner):
        """
        A syntactic-sugar method for finding a cat by its slug and owner.
        """
        return cls.get_by_slug(slug_name, slug_index_parent=owner)
    

class GeneSlugWithParentTest(TestCase):
    def setUp(self):
        # Owners
        self.thomas = Person(slug_name='thomas', name='Thomas')
        self.barack = Person(slug_name='barack', name='Barack')
        
        # Thomas' dogs
        self.babbage = Dog(name='Babbage', owner=self.thomas)
        self.babbage.put_with_slug(
            self.babbage.name, slug_index_parent=self.babbage.owner
        )
        self.pascal = Dog(
            slug_name='pascal',
            slug_index_parent=self.thomas,
            name='Pascal',
            owner=self.thomas
        )
        
        # Barack's dogs
        self.hope = Dog(name='Hope', owner=self.barack)
        self.hope.put_with_slug(
            self.hope.name, slug_index_parent=self.hope.owner
        )
        self.change = Dog(name='Change', owner=self.barack)
        self.change.put_with_slug(
            self.change.name,
            slug_index_parent=self.change.owner
        )
        
        # Barack's cat
        self.hope_the_cat = Cat(name='Hope', owner=self.barack)
    
    def test_setup(self):
        self.assertEqual(self.babbage.slug_name, 'babbage')
        self.assertEqual(
            self.babbage.slug_index.name,
            self.babbage.kind()
        )
        self.assertEqual(
            self.babbage.slug_index.parent_key(), self.thomas.key()
        )
        self.assertEqual(self.pascal.slug_name, 'pascal')
        self.assertEqual(
            self.pascal.slug_index.name,
            self.pascal.kind()
        )
        self.assertEqual(
            self.pascal.slug_index.parent_key(), self.thomas.key()
        )
        self.assertEqual(
            self.babbage.slug_index.key(),
            self.pascal.slug_index.key()
        )
        self.assertEqual(self.hope.slug_name, 'hope')
        self.assertEqual(
            self.hope.slug_index.name,
            self.hope.kind()
        )
        self.assertEqual(
            self.hope.slug_index.parent_key(), self.barack.key()
        )
        self.assertEqual(self.change.slug_name, 'change')
        self.assertEqual(
            self.change.slug_index.name,
            self.change.kind()
        )
        self.assertEqual(
            self.change.slug_index.parent_key(), self.barack.key()
        )
        self.assertEqual(
            self.hope.slug_index.key(),
            self.change.slug_index.key()
        )
        self.assertEqual(self.hope_the_cat.slug_name, 'hope')
        self.assertEqual(
            self.hope_the_cat.slug_index.name,
            self.hope_the_cat.kind()
        )
        self.assertEqual(
            self.hope_the_cat.slug_index.parent_key(), self.barack.key()
        )
    
    def test_get_by_slug(self):
        slug_name = self.babbage.slug_name
        lookup = Dog.get_by_slug(
            slug_name, slug_index_parent=self.thomas
        )
        self.assertEqual(lookup.key(), self.babbage.key())
        lookup = Dog.get_by_slug(
            slug_name, slug_index_parent=self.barack
        )
        self.failIf(lookup)
        self.babbage.delete()
        lookup = Dog.get_by_slug(
            slug_name, slug_index_parent=self.thomas
        )
        self.failIf(lookup)
        slug_name = self.hope_the_cat.slug_name
        lookup = Cat.get_by_slug(
            slug_name, slug_index_parent=self.barack
        )
        self.assertEqual(lookup.key(), self.hope_the_cat.key())
        lookup = Cat.get_by_slug(
            slug_name, slug_index_parent=self.thomas
        )
        self.failIf(lookup)
        self.hope_the_cat.delete()
        lookup = Cat.get_by_slug(
            slug_name, slug_index_parent=self.barack
        )
        self.failIf(lookup)
    
    def test_get_by_slug_and_owner(self):
        slug_name = self.babbage.slug_name
        lookup = Dog.get_by_slug_and_owner(slug_name, self.thomas)
        self.assertEqual(lookup.key(), self.babbage.key())
        lookup = Dog.get_by_slug_and_owner(slug_name, self.barack)
        self.failIf(lookup)
        self.babbage.delete()
        lookup = Dog.get_by_slug_and_owner(slug_name, self.thomas)
        self.failIf(lookup)
        slug_name = self.hope_the_cat.slug_name
        lookup = Cat.get_by_slug_and_owner(slug_name, self.barack)
        self.assertEqual(lookup.key(), self.hope_the_cat.key())
        lookup = Cat.get_by_slug_and_owner(slug_name, self.thomas)
        self.failIf(lookup)
    
    def test_duplicate_slug(self):
        slug_name = self.babbage.slug_name
        slug_index_parent = self.babbage.slug_index.parent()
        dog = Dog(
            slug_name=slug_name, slug_index_parent=slug_index_parent
        )
        self.assertEqual(dog.slug_name, '%s-1' % slug_name)
        dog = Dog(name=self.babbage.name, owner=self.babbage.owner)
        dog.put()
        try:
            dog.put_with_slug(
                slug_name,
                slug_index_parent=slug_index_parent,
                improvise=False
            )
            self.fail()
        except db.BadValueError:
            pass
        dog.put_with_slug('babbage', slug_index_parent=self.barack)
        self.assertEqual(dog.slug_name, 'babbage')
        self.assertNotEqual(
            dog.slug_entity.key(), self.babbage.slug_entity.key()
        )
        self.assertNotEqual(
            dog.slug_index.key(), self.babbage.slug_index.key()
        )
    
    def test_delete_index(self):
        self.assertEqual(GeneSlugIndex.all().count(), 4)
        self.assertEqual(GeneSlug.all().count(), 7)
        self.babbage.slug_index.delete()
        self.assertEqual(GeneSlugIndex.all().count(), 3)
        self.assertEqual(GeneSlug.all().count(), 5)
    
    def test_set_before_put(self):
        slug_name = 'spot'
        slug_index_parent = self.babbage.slug_index.parent()
        dog = Dog()
        dog.put_with_slug(
            slug_name, slug_index_parent=slug_index_parent
        )
        self.assertEqual(dog.slug_name, 'spot')
    
    def test_reserved_slugs(self):
        reserved_slugs = ['foo', 'goo']
        slug_name = reserved_slugs[0]
        slug_index_parent = self.babbage.slug_index.parent()
        dog = Dog(
            slug_name=slug_name,
            slug_index_parent=slug_index_parent,
            reserved_slugs=reserved_slugs,
            name='Foo',
            owner=self.babbage.owner
        )
        self.assertEqual(dog.slug_name, '%s-1' % slug_name)
        dog = Dog(name='Foo', owner=self.babbage.owner)
        dog.put_with_slug(
            slug_name,
            slug_index_parent=slug_index_parent,
            reserved_slugs=reserved_slugs
        )
        self.assertEqual(dog.slug_name, '%s-2' % slug_name)
        try:
            self.pascal.put_with_slug(
                slug_name,
                slug_index_parent=slug_index_parent,
                reserved_slugs=reserved_slugs,
                improvise=False
            )
            self.fail()
        except db.BadValueError:
            pass
        self.assertEqual(self.pascal.slug_name, 'pascal')
        slug_name = reserved_slugs[1]
        dog = Dog(
            slug_name=slug_name,
            slug_index_parent=slug_index_parent,
            reserved_slugs=reserved_slugs,
            name='Goo',
            owner=self.babbage.owner
        )
        self.assertEqual(dog.slug_name, '%s-1' % slug_name)
    
    def test_set_none_slug(self):
        self.babbage.put_with_slug(None, slug_index_parent=self.thomas)
        self.assertEqual(GeneSlug.all().count(), 6)
    
    def test_delete_slug(self):
        self.babbage.delete()
        self.assertEqual(GeneSlug.all().count(), 6)
    

