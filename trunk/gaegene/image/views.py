import logging
import time

from django.http import HttpResponse, Http404
from django.utils.http import http_date
from django.utils.hashcompat import md5_constructor
from google.appengine.api import images
from google.appengine.ext import db

from gaegene.image.models import GeneImage


def serve_image(
        request, image,
        width=None, height=None, encoding=None,
        last_modified=None, use_etag=True
    ):
    if image:
        image = image.get_or_create_image(
            width=width, height=height, encoding=encoding
        )
    if not image:
        raise Http404
    response = HttpResponse(image.image_bytes, image.mime_type)
    # Addn'l headers to explore
    #response['Expires'] = http_date(epoch_seconds=epoch_seconds+300)
    #response['Cache-Control'] = "Private"
    if use_etag:
        response['ETag'] = '"%s"' % (
            md5_constructor(response.content).hexdigest(),
        )
    if last_modified is None:
        last_modified = time.mktime(image.created.timetuple())
    response['Last-Modified'] = http_date(epoch_seconds=last_modified)
    return response

def serve(request, image_key, width=None, height=None, extension='jpg'):
    encoding = None
    if extension.lower() == 'jpg' or extension.lower() == 'jpeg':
        encoding = images.JPEG
    if extension.lower() == 'png':
        encoding = images.PNG
    if encoding is None:
        raise Http404
    image = GeneImage.get(db.Key(encoded=image_key))
    return serve_image(
        request, image,
        width=width, height=height, encoding=encoding
    )

