from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^$', 'manity.views.index'),
    (r'^purchase/$', 'manity.views.purchase'),
    (r'^paypal/pdt/', include('paypal.standard.pdt.urls')),
)

