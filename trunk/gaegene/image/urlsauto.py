from django.conf.urls.defaults import *


urlpatterns = patterns('',
    (r'^image/', include('gaegene.image.urls')),
)
