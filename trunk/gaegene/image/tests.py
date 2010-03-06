import logging
import time

from django.core.urlresolvers import reverse
from django.test import TestCase
from django.utils.http import http_date
from django.utils.hashcompat import md5_constructor
from django.utils.translation import ugettext as _
from google.appengine.api import images
from ragendja.testutils import ModelTestCase

from gaegene.image.models import GeneImage, image_info

TEST_IMAGE_NAME = 'my_image'
TEST_JPEG_PATH = 'media/appengine-noborder-120x30.jpg'
TEST_PNG_PATH = 'media/appengine-noborder-120x30.png'


def create_test_image(path=None, width=None, height=None, encoding=None):
    if path is None:
        path = TEST_JPEG_PATH
    image_file = open(path)
    image_bytes = image_file.read()
    image = GeneImage.create(
        TEST_IMAGE_NAME, image_bytes,
        width=width,
        height=height,
        encoding=encoding
    )
    image_file.close()
    return image, image_bytes


class GeneImageModelTest(ModelTestCase):
    model = GeneImage
    
    def setUp(self):
        self.logging_level = logging.getLogger().getEffectiveLevel()
        logging.disable(logging.CRITICAL)
    
    def tearDown(self):
        logging.disable(self.logging_level)
    
    def assert_image_info(
            self, image, expected_encoding, expected_width, expected_height
        ):
        encoding, width, height = image_info(image.image_bytes)
        self.assertEqual(encoding, expected_encoding)
        self.assertEqual(width, expected_width)
        self.assertEqual(height, expected_height)
    
    def test_create(self):
        image, image_bytes = create_test_image()
        self.failUnless(image)
        self.validate_state(
            (
                'name', 'image_bytes', 'image_url', 'requested_width', 'requested_height',
                'actual_width', 'actual_height', 'encoding'
            ),
            (
                TEST_IMAGE_NAME, image_bytes, None, 120, 30, 120, 30, images.JPEG
            )
        )
        self.assertEqual(image.transformed.count(), 0)
        self.assert_image_info(image, images.JPEG, 120, 30)
        self.assertEqual(image.mime_type, 'image/jpeg')
        image2, image_bytes2 = create_test_image(encoding=images.PNG)
        image_bytes2 = image2.image_bytes
        self.failUnless(image2)
        self.validate_state(
            (
                'name', 'image_bytes', 'image_url', 'requested_width', 'requested_height',
                'actual_width', 'actual_height', 'encoding'
            ),
            (
                TEST_IMAGE_NAME, image_bytes, None, 120, 30, 120, 30, images.JPEG
            ),
            (
                TEST_IMAGE_NAME, image_bytes2, None, 120, 30, 120, 30, images.PNG
            )
        )
        self.assertEqual(image2.transformed.count(), 0)
        self.assert_image_info(image2, images.PNG, 120, 30)
        self.assertEqual(image2.mime_type, 'image/png')
    
    def test_create_url(self):
        image = GeneImage.create(
            TEST_IMAGE_NAME, image_url='http://code.google.com/appengine/images/appengine-noborder-120x30.gif',
            encoding=images.JPEG
        )
        self.failUnless(image)
        self.failUnless(image.image_bytes)
        self.validate_state(
            (
                'name', 'image_url', 'requested_width', 'requested_height',
                'actual_width', 'actual_height', 'encoding'
            ),
            (
                TEST_IMAGE_NAME, 'http://code.google.com/appengine/images/appengine-noborder-120x30.gif', 120, 30, 120, 30, images.JPEG
            )
        )
        self.assertEqual(image.transformed.count(), 0)
        self.assert_image_info(image, images.JPEG, 120, 30)
        self.assertEqual(image.mime_type, 'image/jpeg')
        image2 = GeneImage.create(
            TEST_IMAGE_NAME, image_url='http://code.google.com/appengine/images/appengine-noborder-120x30.gif',
            encoding=images.PNG
        )
        self.failUnless(image2)
        self.failUnless(image2.image_bytes)
        self.validate_state(
            (
                'name', 'image_url', 'requested_width', 'requested_height',
                'actual_width', 'actual_height', 'encoding'
            ),
            (
                TEST_IMAGE_NAME, 'http://code.google.com/appengine/images/appengine-noborder-120x30.gif', 120, 30, 120, 30, images.JPEG
            ),
            (
                TEST_IMAGE_NAME, 'http://code.google.com/appengine/images/appengine-noborder-120x30.gif', 120, 30, 120, 30, images.PNG
            )
        )
        self.assertEqual(image2.transformed.count(), 0)
        self.assert_image_info(image2, images.PNG, 120, 30)
        self.assertEqual(image2.mime_type, 'image/png')
    
    def test_orignal(self):
        image, image_bytes = create_test_image()
        # Do nothing
        scaled_image = image.get_or_create_image(
            width=None, height=None, encoding=None
        )
        self.assertEqual(scaled_image, image)
        self.assert_image_info(scaled_image, images.JPEG, 120, 30)
    
    def test_scale_width(self):
        image, image_bytes = create_test_image()
        self.assertEqual(GeneImage.all().count(), 1)
        lookup_image = image.get_or_create_image()
        self.assertEqual(GeneImage.all().count(), 1)
        self.assertEqual(lookup_image, image)
        scaled_image = image.get_or_create_image(
            width=50, height=None, encoding=None
        )
        self.assertEqual(GeneImage.all().count(), 2)
        self.failIfEqual(scaled_image, image)
        self.assert_image_info(scaled_image, images.JPEG, 50, 12)
        lookup_image = image.get_or_create_image(
            width=50, height=None, encoding=None
        )
        self.assertEqual(lookup_image, scaled_image)
        self.assertEqual(GeneImage.all().count(), 2)
        lookup_image = image.get_or_create_image(
            width=None, height=50, encoding=None
        )
        self.assertEqual(lookup_image, scaled_image)
        self.assertEqual(GeneImage.all().count(), 2)
        # Lookup with the scaled image itself
        lookup_image = scaled_image.get_or_create_image(
            width=50, height=None, encoding=None
        )
        self.assertEqual(lookup_image, scaled_image)
        self.assertEqual(GeneImage.all().count(), 2)
        # Lookup by actual dimensions
        lookup_image = image.get_or_create_image(
            width=50, height=12, encoding=None
        )
        self.assertEqual(lookup_image, scaled_image)
        self.assertEqual(GeneImage.all().count(), 2)
    
    def test_scale_height(self):
        image, image_bytes = create_test_image()
        scaled_image = image.get_or_create_image(
            width=None, height=50, encoding=None
        )
        self.failIfEqual(scaled_image, image)
        self.assert_image_info(scaled_image, images.JPEG, 50, 12)
        lookup_image = image.get_or_create_image(
            width=None, height=50, encoding=None
        )
        self.assertEqual(lookup_image, scaled_image)
        lookup_image = image.get_or_create_image(
            width=50, height=None, encoding=None
        )
        self.assertEqual(lookup_image, scaled_image)
        # Lookup with the scaled image itself
        lookup_image = scaled_image.get_or_create_image(
            width=None, height=50, encoding=None
        )
        self.assertEqual(lookup_image, scaled_image)
        # Lookup by actual dimensions
        lookup_image = image.get_or_create_image(
            width=50, height=12, encoding=None
        )
        self.assertEqual(lookup_image, scaled_image)
    
    def test_encode_png(self):
        image, image_bytes = create_test_image()
        encoded_image = image.get_or_create_image(
            width=None, height=None, encoding=images.JPEG
        )
        self.assertEqual(encoded_image, image)
        encoded_image = image.get_or_create_image(
            width=None, height=None, encoding=images.PNG
        )
        self.failIfEqual(encoded_image, image)
        self.assert_image_info(encoded_image, images.PNG, 120, 30)
    
    def test_encode_jpg(self):
        image, image_bytes = create_test_image(path=TEST_PNG_PATH)
        encoded_image = image.get_or_create_image(
            width=None, height=None, encoding=images.PNG
        )
        self.assertEqual(encoded_image, image)
        encoded_image = image.get_or_create_image(
            width=None, height=None, encoding=images.JPEG
        )
        self.failIfEqual(encoded_image, image)
        self.assert_image_info(encoded_image, images.JPEG, 120, 30)
    
    def test_pixels_png(self):
        image, image_bytes = create_test_image(path=TEST_PNG_PATH)
        pixels = image.pixels
        self.failUnless(pixels)
        pixel_list = [row for row in pixels]
        self.assertEqual(image.actual_height, len(pixel_list))
        self.assertEqual(image.actual_width * 3, len(pixel_list[0]))
    
    def test_pixels_jpg(self):
        image, image_bytes = create_test_image(path=TEST_JPEG_PATH)
        try:
            pixels = image.pixels
            self.fail("Shouldn't be able to get pixels of JPEGs")
        except NotImplementedError:
            pass
    
    def test_delete(self):
        image, image_bytes = create_test_image()
        encoded_image = image.get_or_create_image(
            width=None, height=None, encoding=images.PNG
        )
        scaled_width_image = image.get_or_create_image(
            width=50, height=None, encoding=None
        )
        scaled_height_image = image.get_or_create_image(
            width=None, height=100, encoding=None
        )
        self.assertEqual(image.transformed.count(), 3)
        scaled_height_image.delete()
        self.assertEqual(GeneImage.all().count(), 3)
        self.assertEqual(image.transformed.count(), 2)
        image.delete()
        self.assertEqual(GeneImage.all().count(), 0)
    

class GeneImageViewTest(TestCase):
    def assert_http_response_code_content_type(
            self, response, url, code, content_type
        ):
        self.failUnlessEqual(
            code,
            response.status_code,
            "%s status_code=%s (expected status_code is %s)" % (
                url, response.status_code, str(code)
            )
        )
        self.failUnlessEqual(
            response._headers['content-type'],
            ('Content-Type', content_type)
        )
    
    def setUp(self):
        self.image, self.image_bytes = create_test_image()
    
    def test_jpg(self):
        url = reverse(
            'image_serve',
            kwargs={
                'image_key' : str(self.image.key()),
                'extension' : 'jpg'
            }
        )
        response = self.client.get(url)
        self.assert_http_response_code_content_type(
            response, url, 200, 'image/jpeg'
        )
        self.assertEqual(response.content, self.image_bytes)
        url = reverse(
            'image_serve',
            kwargs={
                'image_key' : str(self.image.key()),
                'extension' : 'jpeg'
            }
        )
        response = self.client.get(url)
        self.assert_http_response_code_content_type(
            response, url, 200, 'image/jpeg'
        )
        self.assertEqual(response.content, self.image_bytes)
    
    def test_jpg_scale(self):
        url = reverse(
            'image_serve_scaled',
            kwargs={
                'image_key' : str(self.image.key()),
                'width' : 32,
                'height' : 32,
                'extension' : 'jpg'
            }
        )
        response = self.client.get(url)
        self.assert_http_response_code_content_type(
            response, url, 200, 'image/jpeg'
        )
        scaled_image, scaled_image_bytes = create_test_image(
            width=32, height=32
        )
        self.assertEqual(response.content, scaled_image.image_bytes)
    
    def test_png(self):
        url = reverse(
            'image_serve',
            kwargs={
                'image_key' : str(self.image.key()),
                'extension' : 'png'
            }
        )
        response = self.client.get(url)
        self.assert_http_response_code_content_type(
            response, url, 200, 'image/png'
        )
        encoded_image, encoded_image_bytes = create_test_image(
            encoding=images.PNG
        )
        self.assertEqual(response.content, encoded_image.image_bytes)
    
    def test_png_scale(self):
        url = reverse(
            'image_serve_scaled',
            kwargs={
                'image_key' : str(self.image.key()),
                'width' : 32,
                'height' : 32,
                'extension' : 'png'
            }
        )
        response = self.client.get(url)
        self.assert_http_response_code_content_type(
            response, url, 200, 'image/png'
        )
        scaled_image, scaled_image_bytes = create_test_image(
            width=32, height=32, encoding=images.PNG
        )
        self.assertEqual(response.content, scaled_image.image_bytes)
    
    def test_response_headers(self):
        url = reverse(
            'image_serve',
            kwargs={
                'image_key' : str(self.image.key()),
                'extension' : 'jpg'
            }
        )
        response = self.client.get(url)
        self.assert_http_response_code_content_type(
            response, url, 200, 'image/jpeg'
        )
        response_items = response.items()
        etag = None
        last_modified = None
        for item in response_items:
            if item[0] == 'Last-Modified':
                last_modified = item[1]
            if item[0] == 'ETag':
                etag = item[1]
        self.assertEqual(
            etag, '"%s"' % md5_constructor(response.content).hexdigest()
        )
        epoch_seconds = time.mktime(self.image.created.timetuple())
        self.assertEqual(
            last_modified, http_date(epoch_seconds=epoch_seconds)
        )
    

