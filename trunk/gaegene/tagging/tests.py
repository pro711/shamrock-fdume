from django.test import TestCase
from google.appengine.ext import db
from ragendja.testutils import ModelTestCase

from gaegene.tagging.models import GeneTag, GeneTaggable, Cloud


TEST_TAGNAME = 'test-tag'
TEST_TAGNAME2 = 'test-tag-2'
TEST_TAGNAME3 = 'test-tag-3'
TEST_TAGNAME4 = 'test-tag-4'

class TaggableModel(GeneTaggable):
    name = db.StringProperty(required=False, default='test')

class OtherTaggableModel(GeneTaggable):
    pass

class GeneTaggableTest(ModelTestCase):
    model = GeneTaggable
        
    def test_add_tag(self):
        taggable = GeneTaggable()
        taggable.put()
        taggable.tag_append(TEST_TAGNAME)
        tagnames = taggable.tagnames
        self.failUnless(tagnames)
        self.assertEqual(tagnames[0], TEST_TAGNAME)
        taggables = GeneTaggable.taggables(TEST_TAGNAME)
        self.failUnless(taggables)
        self.assertEqual(taggables[0], taggable)
    
    def test_add_tag_twice(self):
        taggable = GeneTaggable()
        taggable.put()
        taggable.tag_append(TEST_TAGNAME)
        taggable.tag_append(TEST_TAGNAME)
        taggable.put()
        self.assertEqual(1, len(taggable.tagnames))
        
    def test_tag_multiple_types(self):
        taggable = TaggableModel()
        taggable.put()
        other_taggable = OtherTaggableModel()
        other_taggable.put()
        taggable.tag_append(TEST_TAGNAME)
        other_taggable.tag_append(TEST_TAGNAME)
        taggables = TaggableModel.taggables(TEST_TAGNAME)
        self.assertEqual(1, len(taggables))
        self.failUnless(isinstance(taggables[0], TaggableModel))
        taggables = OtherTaggableModel.taggables(TEST_TAGNAME)
        self.assertEqual(1, len(taggables))
        self.failUnless(isinstance(taggables[0], OtherTaggableModel))
    
    def test_remove_tag(self):
        taggable = GeneTaggable()
        taggable.put()
        taggable2 = GeneTaggable()
        taggable2.put()
        taggable.tag_append(TEST_TAGNAME)
        taggable2.tag_append(TEST_TAGNAME)
        taggable.tag_remove(TEST_TAGNAME)
        taggables = GeneTaggable.taggables(TEST_TAGNAME)
        self.assertEqual(1, len(taggables))
        self.assertEquals(taggable2, taggables[0])
        self.assertEquals(0, len(taggable.tagnames))
    
    def test_remove_tag_twice(self):
        taggable = GeneTaggable()
        taggable.put()
        taggable.tag_append(TEST_TAGNAME)
        taggable.tag_remove(TEST_TAGNAME)
        self.assertEqual(0, len(taggable.tagnames))
        try:
            taggable.tag_remove(TEST_TAGNAME)
        except:
            self.fail('Removing tag should not throw an exception when not found in list')
        self.assertEqual(0, len(taggable.tagnames))
    
    def test_tag_as_csv(self):
        taggable = GeneTaggable()
        taggable.put()
        taggable.tag_append(TEST_TAGNAME)
        taggable.set_tagnames_csv("  foo boo       , bar, baz")
        self.failUnlessEqual("foo-boo, bar, baz", taggable.tagnames_csv)
    

# class GeneTagTest(ModelTestCase):
#     model = GeneTag
#     
#     def test_add_tag(self):
#         taggable = GeneTaggable()
#         taggable.put()
#         taggable.tag_append(TEST_TAGNAME)
#         tag = GeneTag.get_by_key_name(GeneTag.key_name(TEST_TAGNAME))
#         self.failUnless(tag)
#         self.assertEqual(tag.live_count, 1)
#     
#     def test_add_tag_twice(self):
#         taggable = GeneTaggable()
#         taggable.put()
#         taggable.tag_append(TEST_TAGNAME)
#         taggable.tag_append(TEST_TAGNAME)
#         tag = GeneTag.get_by_key_name(GeneTag.key_name(TEST_TAGNAME))
#         self.failUnless(tag)
#         self.assertEqual(tag.live_count, 1)
#         
#     def test_tag_multiple_types(self):
#         taggable = TaggableModel()
#         taggable.put()
#         other_taggable = OtherTaggableModel()
#         other_taggable.put()
#         taggable.tag_append(TEST_TAGNAME)
#         other_taggable.tag_append(TEST_TAGNAME)
#         tag = GeneTag.get_by_key_name(GeneTag.key_name(TEST_TAGNAME))
#         self.failUnless(tag)
#         self.assertEqual(tag.live_count, 2)
#     
#     def test_remove_tag(self):
#         taggable = GeneTaggable()
#         taggable.put()
#         taggable2 = GeneTaggable()
#         taggable2.put()
#         taggable.tag_append(TEST_TAGNAME)
#         taggable2.tag_append(TEST_TAGNAME)
#         taggable.tag_remove(TEST_TAGNAME)
#         tag = GeneTag.get_by_key_name(GeneTag.key_name(TEST_TAGNAME))
#         self.failUnless(tag)
#         self.assertEqual(tag.live_count, 1)
#     
#     def test_remove_tag_twice(self):
#         taggable = GeneTaggable()
#         taggable.put()
#         taggable.tag_append(TEST_TAGNAME)
#         taggable.tag_remove(TEST_TAGNAME)
#         taggable.tag_remove(TEST_TAGNAME)
#         tag = GeneTag.get_by_key_name(GeneTag.key_name(TEST_TAGNAME))
#         self.failUnless(tag)
#         self.assertEqual(tag.live_count, 0)
#     
# 
class CloudTest(TestCase):
    def setUp(self):
        pass
    
    def test_construct_with_strings(self):
        cloud = Cloud(
            tagnames=[TEST_TAGNAME, TEST_TAGNAME2, TEST_TAGNAME3]
        )
        self.assertEqual(cloud.tagnames[0], TEST_TAGNAME)
        self.assertEqual(cloud.tagnames[1], TEST_TAGNAME2)
        self.assertEqual(cloud.tagnames[2], TEST_TAGNAME3)
        cloud = Cloud(tagnames=[TEST_TAGNAME4,])
        self.assertEqual(cloud.tagnames[0], TEST_TAGNAME4)
    
    def test_get_ranked_tags(self):
        taggable = GeneTaggable()
        taggable.put()
        taggable2 = GeneTaggable()
        taggable2.put()
        taggable3 = GeneTaggable()
        taggable3.put()
        taggable.tag_append(TEST_TAGNAME)
        taggable.tag_append(TEST_TAGNAME2)
        taggable2.tag_append(TEST_TAGNAME)
        taggable3.tag_append(TEST_TAGNAME2)
        
        cloud = taggable2.cloud
        ranked_tags = cloud.ranked_tags
        self.failUnless(ranked_tags.has_key(TEST_TAGNAME))
        self.failUnless(ranked_tags.has_key(TEST_TAGNAME2))
        self.failIf(ranked_tags.has_key(TEST_TAGNAME3))
        self.assertEqual(2, ranked_tags[TEST_TAGNAME])
        self.assertEqual(1, ranked_tags[TEST_TAGNAME2])
        self.assertEqual(2, cloud.max_rank)
        self.assertEqual(1, cloud.min_rank)
    
    def test_get_ranked_tags_single_root(self):
        taggable = GeneTaggable()
        taggable.put()
        taggable2 = GeneTaggable()
        taggable2.put()
        taggable3 = GeneTaggable()
        taggable3.put()
        taggable.tag_append(TEST_TAGNAME)
        taggable.tag_append(TEST_TAGNAME2)
        taggable2.tag_append(TEST_TAGNAME)
        taggable3.tag_append(TEST_TAGNAME2)
        
        cloud = Cloud(tagnames=[TEST_TAGNAME,])
        ranked_tags = cloud.ranked_tags
        self.failUnless(ranked_tags.has_key(TEST_TAGNAME))
        self.failUnless(ranked_tags.has_key(TEST_TAGNAME2))
        self.failIf(ranked_tags.has_key(TEST_TAGNAME3))
        self.assertEqual(2, ranked_tags[TEST_TAGNAME])
        self.assertEqual(1, ranked_tags[TEST_TAGNAME2])
        self.assertEqual(2, cloud.max_rank)
        self.assertEqual(1, cloud.min_rank)
    
    def test_get_ranked_tags_single_root_with_type(self):
        taggable = TaggableModel()
        taggable.put()
        other_taggable = OtherTaggableModel()
        other_taggable.put()
        taggable2 = TaggableModel()
        taggable2.put()
        taggable.tag_append(TEST_TAGNAME)
        taggable.tag_append(TEST_TAGNAME2)
        other_taggable.tag_append(TEST_TAGNAME)
        taggable2.tag_append(TEST_TAGNAME2)
        cloud = Cloud(
            tagnames=[TEST_TAGNAME,], taggable_model=TaggableModel
        )
        ranked_tags = cloud.ranked_tags
        self.failUnless(ranked_tags.has_key(TEST_TAGNAME))
        self.failUnless(ranked_tags.has_key(TEST_TAGNAME2))
        self.failIf(ranked_tags.has_key(TEST_TAGNAME3))
        self.assertEqual(1, ranked_tags[TEST_TAGNAME])
        self.assertEqual(1, ranked_tags[TEST_TAGNAME2])
        self.assertEqual(1, cloud.max_rank)
        self.assertEqual(1, cloud.min_rank)
    
    def test_get_ranked_tags_multi_root(self):
        taggable = GeneTaggable()
        taggable.put()
        taggable2 = GeneTaggable()
        taggable2.put()
        taggable3 = GeneTaggable()
        taggable3.put()
        taggable.tag_append(TEST_TAGNAME)
        taggable.tag_append(TEST_TAGNAME2)
        taggable2.tag_append(TEST_TAGNAME)
        taggable3.tag_append(TEST_TAGNAME2)
        
        cloud = taggable.cloud
        ranked_tags = cloud.ranked_tags
        
        self.failUnless(ranked_tags.has_key(TEST_TAGNAME))
        self.failUnless(ranked_tags.has_key(TEST_TAGNAME2))
        self.failIf(ranked_tags.has_key(TEST_TAGNAME3))
        self.assertEqual(2, ranked_tags[TEST_TAGNAME])
        self.assertEqual(2, ranked_tags[TEST_TAGNAME2])
        self.assertEqual(2, cloud.max_rank)
        self.assertEqual(2, cloud.min_rank)
    
    def test_get_ranked_tags_multi_root_with_type(self):
        taggable = TaggableModel()
        taggable.put()
        other_taggable = OtherTaggableModel()
        other_taggable.put()
        taggable2 = TaggableModel()
        taggable2.put()
        
        taggable.tag_append(TEST_TAGNAME)
        taggable.tag_append(TEST_TAGNAME2)
        other_taggable.tag_append(TEST_TAGNAME)
        taggable2.tag_append(TEST_TAGNAME2)
        
        cloud = taggable.cloud
        ranked_tags = cloud.ranked_tags
        self.failUnless(ranked_tags.has_key(TEST_TAGNAME))
        self.failUnless(ranked_tags.has_key(TEST_TAGNAME2))
        self.failIf(ranked_tags.has_key(TEST_TAGNAME3))
        self.assertEqual(1, ranked_tags[TEST_TAGNAME])
        self.assertEqual(2, ranked_tags[TEST_TAGNAME2])
        self.assertEqual(2, cloud.max_rank)
        self.assertEqual(1, cloud.min_rank)
    
    def test_min_max_rank_empty_set(self):
        cloud = Cloud(tagnames=['notatag'])
        self.assertEqual(0, cloud.max_rank)
        self.assertEqual(0, cloud.min_rank)
    
    def test_filter_cloud(self):
        taggable = TaggableModel(name='one')
        taggable.put()
        taggable2 = TaggableModel(name='two')
        taggable2.put()
        taggable3 = TaggableModel(name='three')
        taggable3.put()
        
        taggable.tag_append(TEST_TAGNAME)
        taggable.tag_append(TEST_TAGNAME2)
        taggable2.tag_append(TEST_TAGNAME)
        taggable2.tag_append(TEST_TAGNAME3)
        taggable3.tag_append(TEST_TAGNAME3)
        
        cloud = Cloud(
            tagnames=[TEST_TAGNAME, TEST_TAGNAME2],
            taggable_model=TaggableModel,
            taggable_filter=lambda taggable: taggable.name == 'one')
        ranked_tags = cloud.ranked_tags
        self.failUnless(ranked_tags.has_key(TEST_TAGNAME))
        self.failUnless(ranked_tags.has_key(TEST_TAGNAME2))
        self.failIf(ranked_tags.has_key(TEST_TAGNAME3)) # Should be filtered.  Only tags on taggable should get through.
        self.assertEqual(1, ranked_tags[TEST_TAGNAME])
        self.assertEqual(1, ranked_tags[TEST_TAGNAME2])
        self.assertEqual(1, cloud.max_rank)
        self.assertEqual(1, cloud.min_rank)
        
        cloud = Cloud(
            tagnames=[TEST_TAGNAME, TEST_TAGNAME2],
            taggable_model=TaggableModel,
            taggable_filter=lambda taggable: taggable.name != 'one')
        ranked_tags = cloud.ranked_tags
        self.failUnless(ranked_tags.has_key(TEST_TAGNAME))
        self.failIf(ranked_tags.has_key(TEST_TAGNAME2)) # Should be filtered.  Only exists on taggable, which is filtered out.
        self.failUnless(ranked_tags.has_key(TEST_TAGNAME3)) 
        self.assertEqual(1, ranked_tags[TEST_TAGNAME])
        self.assertEqual(1, ranked_tags[TEST_TAGNAME3])
        self.assertEqual(1, cloud.max_rank)
        self.assertEqual(1, cloud.min_rank)
    

