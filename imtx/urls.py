import os
from django.conf import settings
from django.contrib import admin
from django.conf.urls import *
from django.contrib.sitemaps import Sitemap
from django.contrib.sitemaps import views as sitemap_views
from django.views.decorators.cache import cache_page
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from tastypie.api import Api
from lovekindle.api.resources import BookResource

from imtx.apps.blog.models import Post, Category
from imtx.apps.blog.feeds import LatestPosts, LatestCommentFeed

admin.autodiscover()

v1_api = Api(api_name='v1')
v1_api.register(BookResource())

class PostSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.2

    def items(self):
        return Post.objects.get_post()

    def lastmod(self, obj):
        return obj.date

sitemaps = {
    'posts': PostSitemap,
}

urlpatterns = patterns('',
    (r'^sitemap.xml$', cache_page(60 * 60 * 6)(sitemap_views.sitemap),  {'sitemaps': sitemaps}),
#    (r'^zhejiangpm25$', 'imtx.views.zhejiangpm25'),
    (r'^admin/', include(admin.site.urls)),
    (r'^wechat/', include('wechat.urls')),
    url(r'^feed/latest/$', LatestPosts(), name='feed'),
    url(r'^feed/comments/$', LatestCommentFeed()),
    (r'^comment/', include('imtx.apps.comments.urls')),
    (r'^comments/$', 'imtx.apps.comments.views.comment_list'),
    (r'^xmlrpc/$', 'django_xmlrpc.views.handle_xmlrpc', {}, 'xmlrpc'),
    (r'^api/', include(v1_api.urls)),
)

urlpatterns += patterns('imtx.apps.blog.views',
    (r'^upload/$', 'upload'),
    (r'^search/', 'search'),
    (r'^feed/$', 'redirect_feed'),
    (r'^rss/$', 'redirect_feed'),
    url(r'^tag/(?P<name>.*)/$', 'tag_view', name='tag-view'),
    (r'^$', 'index'),
    (r'^index.html$', 'index'),
    (r'^stats/$', 'stats'),
    (r'^archives/$', 'index'),
    url(r'^archives/(?P<post_id>\d+).html$', 'single_post', name='single_post'),
    url(r'^archives/category/(?P<slug>[-\w]+)/$', 'category_view', name='post-category'),
    (r'^archives/(?P<year>\d{4})/(?P<month>\d{1,2})/$', 'archive_view'),
    url(r'^([-\w]+)/$', 'static_pages', name='static_pages'),
)

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT}),
    )
