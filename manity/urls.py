from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'manity.views.purchase'),
    (r'^purchase/$', 'manity.views.purchase'),
    (r'^paypal/pdt/', include('paypal.standard.pdt.urls')),
)

