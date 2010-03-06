from django.conf.urls.defaults import *

urlpatterns = patterns(
    'gaegene.pagination.tests',
    url(r'^test/$', 'objects', name='pagination_test'),
    url(r'^test_reverse/$', 'objects_reverse', name='pagination_test_reverse')
)
