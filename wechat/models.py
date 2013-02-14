import re
import time

from django.db import models
from django.contrib.sites.models import Site
from django.utils.translation import ugettext_lazy as _

from imtx.apps.blog.models import Post

class WechatUser(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.name

class Article(models.Model):
    post = models.ForeignKey(Post, unique=True)
    count = models.PositiveIntegerField(default=1)

    def __unicode__(self):
        return u"Article: %s" % self.post.title

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            raise KeyError('No "%s" key available for this article' % key)

    @property
    def article_title(self):
        return self.post.title

    @property
    def article_desc(self):
        return self.post.get_description()

    @property
    def article_pic_url(self):
        return self.post.get_media_url()

    @property
    def article_url(self):
        return 'http://%s/wechat/post/%d.html' % (Site.objects.get_current().domain, self.post.id)


class MessageResponse(models.Model):
    MESSAGE_TYPE_CHOICES = (
        ('hello', _('Hello Message')),
        ('text', _('Text Message')),
        ('music', _('Music Message')),
        ('news', _('News Message')),
    )
    message_type = models.CharField(max_length=20, default='text', choices=MESSAGE_TYPE_CHOICES)
    create_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(WechatUser)
    articles = models.ManyToManyField(Article, blank=True, null=True)
    request_content = models.TextField(blank=True)
    response_content = models.TextField(blank=True)

    def __unicode__(self):
        return u"Message: %s from %s" % (self.request_content, self.user.name)

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        else:
            raise KeyError('No "%s" key available for this message' % key)

    @property
    def from_user_name(self):
        return u'imtx-me'

    @property
    def to_user_name(self):
        return self.user.name

    @property
    def article_count(self):
        return self.articles.count()

    @property
    def timestamp(self):
        return time.mktime(self.create_time.timetuple())

    def create_articles_from_posts(self, posts):
        if posts:
            self.message_type = 'news'

            for post in posts:
                article, created = Article.objects.get_or_create(post=post)

                if not created:
                    article.count = article.count + 1
                    article.save()

                self.articles.add(article)
                self.save()

    def build_response_xml(self):
        response_xml = ''

        if self.message_type == 'hello':
            response_xml = '''<xml>
                              <ToUserName><![CDATA[%(to_user_name)s]]></ToUserName>
                              <FromUserName><![CDATA[%(from_user_name)s]]></FromUserName>
                              <CreateTime>%(timestamp)s</CreateTime>
                              <MsgType><![CDATA[text]]></MsgType>
                              <Content><![CDATA[%(response_content)s]]></Content>
                              <FuncFlag>0</FuncFlag>
                              </xml>''' % self
        elif self.message_type == 'text':
            response_xml = '''<xml>
                              <ToUserName><![CDATA[%(to_user_name)s]]></ToUserName>
                              <FromUserName><![CDATA[%(from_user_name)s]]></FromUserName>
                              <CreateTime>%(timestamp)s</CreateTime>
                              <MsgType><![CDATA[text]]></MsgType>
                              <Content><![CDATA[%(response_content)s]]></Content>
                              <FuncFlag>0</FuncFlag>
                              </xml>''' % self
        elif self.message_type == 'news':
            articles_xml = ''
            for article in self.articles.all():
                articles_xml = articles_xml + '''<item>
                             <Title><![CDATA[%(article_title)s]]></Title>
                             <Description><![CDATA[%(article_desc)s]]></Description>
                             <PicUrl><![CDATA[%(article_pic_url)s]]></PicUrl>
                             <Url><![CDATA[%(article_url)s]]></Url>
                             </item>
                             ''' % article

            response_xml = '''<xml>
                             <ToUserName><![CDATA[%(to_user_name)s]]></ToUserName>
                             <FromUserName><![CDATA[%(from_user_name)s]]></FromUserName>
                             <CreateTime>%(timestamp)s</CreateTime>
                             <MsgType><![CDATA[news]]></MsgType>
                             <ArticleCount>%(article_count)d</ArticleCount>
                             <Articles>
                             ''' % self + \
                             articles_xml + \
                           '''</Articles>
                             <FuncFlag>1</FuncFlag>
                             </xml>'''

        return response_xml
