from django.conf.urls.defaults import patterns

urlpatterns = patterns('',
    (r'^$', 'manity.views.index'),
    (r'^purchase/$', 'manity.views.purchase'),
    (r'^pdt/', 'manity.views.pdt'),
)
