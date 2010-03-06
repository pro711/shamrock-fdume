from django.conf.urls.defaults import *


urlpatterns = patterns('',
    (r'^pagination_test/', include('gaegene.pagination.urls')),
)
