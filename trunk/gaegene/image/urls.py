from django.conf.urls.defaults import *


urlpatterns = patterns(
    '', # We're calling django views as well as our own
    url(
        r'^(?P<image_key>.*)-(?P<width>.*)x(?P<height>.*)\.(?P<extension>.*)$',
        'gaegene.image.views.serve',
        name='image_serve_scaled'
    ),
    url(
        r'^(?P<image_key>.*)\.(?P<extension>.*)$',
        'gaegene.image.views.serve',
        name='image_serve'
    )
)
