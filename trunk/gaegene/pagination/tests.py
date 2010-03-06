from django.core.urlresolvers import reverse
from django.test import TestCase
from google.appengine.ext import db

from gaegene.pagination.models import Paginator
from gaegene.pagination.views import object_list


class TestObject(db.Model):
    name = db.StringProperty(required=True)

def create_test_object(index):
    object = TestObject(name="test-%02d" % index)
    object.put()
    return object

# Test views
def objects(request, page_value=None):
    object_query = TestObject.all()
    order_property = 'name'
    template_name = 'pagination/test.html'
    return object_list(
        request, object_query, order_property, template_name,
        paginate_by=5, page_value=page_value
    )

def objects_reverse(request, page_value=None):
    object_query = TestObject.all()
    order_property = '-name'
    template_name = 'pagination/test.html'
    return object_list(
        request, object_query, order_property, template_name,
        paginate_by=5, page_value=page_value
    )


class PaginatorTest(TestCase):
    def setUp(self):
        self.test_objects = []
        for i in range(0, 28):
            self.test_objects.append(create_test_object(i))
    
    def test_paginator(self, paginator=None):
        if not paginator:
            paginator = Paginator(TestObject.all(), 'name', per_page=10)
        page = paginator.page(None)
        self.failUnless(page)
        self.failUnless(page.has_next())
        self.failIf(page.has_previous())
        self.assertEqual(len(page.object_list), 10)
        next_page = paginator.page(page.next_page_value)
        self.failUnless(next_page)
        self.failUnless(next_page.has_next())
        self.failUnless(next_page.has_previous())
        self.assertEqual(len(next_page.object_list), 10)
        self.assertEqual(
            page.next_page_value, next_page.object_list[0].name
        )
        self.assertEqual(
            next_page.previous_page_value, page.object_list[0].name
        )
        last_page = paginator.page(next_page.next_page_value)
        self.failUnless(last_page)
        self.failIf(last_page.has_next())
        self.failUnless(last_page.has_previous())
        self.assertEqual(len(last_page.object_list), 8)
        self.assertEqual(
            next_page.next_page_value, last_page.object_list[0].name
        )
        self.assertEqual(
            last_page.previous_page_value, next_page.object_list[0].name
        )
    
    def test_paginator_reverse(self):
        paginator = Paginator(TestObject.all(), '-name', per_page=10)
        self.test_paginator(paginator=paginator)
    
    def test_start_value(self):
        paginator = Paginator(TestObject.all(), 'name', per_page=10)
        page = paginator.page('test-08')
        self.failUnless(page)
        self.failUnless(page.has_next())
        self.failUnless(page.has_previous())
        self.assertEqual(len(page.object_list), 10)
        self.assertEqual(page.next_page_value, 'test-18')
        next_page = paginator.page(page.next_page_value)
        self.failUnless(next_page)
        self.failIf(next_page.has_next())
        self.failUnless(next_page.has_previous())
        self.assertEqual(next_page.previous_page_value, 'test-08')
    
    def test_start_value_reverse(self):
        paginator = Paginator(TestObject.all(), '-name', per_page=10)
        page = paginator.page('test-20')
        self.failUnless(page)
        self.failUnless(page.has_next())
        self.failUnless(page.has_previous())
        self.assertEqual(len(page.object_list), 10)
        self.assertEqual(page.next_page_value, 'test-10')
        next_page = paginator.page(page.next_page_value)
        self.failUnless(next_page)
        self.failUnless(next_page.has_next())
        self.failUnless(next_page.has_previous())
        self.assertEqual(len(next_page.object_list), 10)
        self.assertEqual(next_page.previous_page_value, 'test-20')
        last_page = paginator.page(next_page.next_page_value)
        self.failUnless(last_page)
        self.failIf(last_page.has_next())
        self.failUnless(last_page.has_previous())
        self.assertEqual(len(last_page.object_list), 1)
    


class ObjectListViewTest(TestCase):
    def setUp(self):
        self.test_objects = []
        for i in range(0, 13):
            self.test_objects.append(create_test_object(i))
    
    def test_objects(self):
        url = reverse('pagination_test')
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        context = response.context
        page = context['page']
        self.failUnless(page)
        self.failUnless(page.has_next())
        self.failIf(page.has_previous())
        self.assertEqual(page.object_list[0].name, 'test-00')
        response = self.client.get(
            url, {'page_value' : page.next_page_value}
        )
        self.failUnlessEqual(response.status_code, 200)
        context = response.context
        page = context['page']
        self.failUnless(page)
        self.failUnless(page.has_next())
        self.failUnless(page.has_previous())
        self.assertEqual(page.object_list[0].name, 'test-05')
    
    def test_objects_reverse(self):
        url = reverse('pagination_test_reverse')
        response = self.client.get(url)
        self.failUnlessEqual(response.status_code, 200)
        context = response.context
        page = context['page']
        self.failUnless(page)
        self.failUnless(page.has_next())
        self.failIf(page.has_previous())
        self.assertEqual(page.object_list[0].name, 'test-12')
        response = self.client.get(
            url, {'page_value' : page.next_page_value}
        )
        self.failUnlessEqual(response.status_code, 200)
        context = response.context
        page = context['page']
        self.failUnless(page)
        self.failUnless(page.has_next())
        self.failUnless(page.has_previous())
        self.assertEqual(page.object_list[0].name, 'test-07')
    

