# coding: utf-8

import re
import time
import random

from lxml import etree
from django.http import HttpResponse
from django.db.models import Q
from django.contrib.sites.models import Site

from imtx.apps.blog.models import Post
from imtx.views import aqi_pm25, aqi_category

def etree_to_dict(t):
    d = {}
    for t in t.iterchildren():
        d[t.tag] = t.text
    return d

def process_request(request):
    request_dict = etree_to_dict(etree.fromstring(request.raw_post_data))
    response_dict = {'FromUserName': 'imtx-me',
                     'ToUserName': request_dict['FromUserName'],
                     'CreateTime': int(time.time())}
    response_xml = ''
    content = request_dict['Content']

    if content == 'Hello2BizUser':
        response_dict['Content'] = u'Hello, 我是TualatriX! 感谢关注IMTX，你可以通过搜索关键字来随机查看我过去写的文章，尝试一下？如: Python。'
        response_xml = '''<xml>
                          <ToUserName><![CDATA[%(ToUserName)s]]></ToUserName>
                          <FromUserName><![CDATA[%(FromUserName)s]]></FromUserName>
                          <CreateTime>%(CreateTime)s</CreateTime>
                          <MsgType><![CDATA[text]]></MsgType>
                          <Content><![CDATA[%(Content)s]]></Content>
                          <FuncFlag>0</FuncFlag>
                          </xml>''' % response_dict
    elif content.isdigit():
        content = int(content)
        response_dict['Content'] = u'AQI: %s, %s' % (aqi_pm25(content), aqi_category(aqi_pm25(content)))
        response_xml = '''<xml>
                          <ToUserName><![CDATA[%(ToUserName)s]]></ToUserName>
                          <FromUserName><![CDATA[%(FromUserName)s]]></FromUserName>
                          <CreateTime>%(CreateTime)s</CreateTime>
                          <MsgType><![CDATA[text]]></MsgType>
                          <Content><![CDATA[%(Content)s]]></Content>
                          <FuncFlag>0</FuncFlag>
                          </xml>''' % response_dict

        return HttpResponse(response_xml, content_type='application/xml')
    else:
        content = request_dict['Content']
        qset = (Q(title__icontains=content) | Q(title__icontains=content))
        posts = Post.objects.filter(qset, status='publish').distinct()

        if posts:
            post = posts[random.randint(0, posts.count() - 1)]
            response_dict['Title'] = post.title
            response_dict['Description'] = post.get_description()
            response_dict['PicUrl'] = post.get_media_url()
            response_dict['Url'] = 'http://%s/wechat/post/%d.html' % (Site.objects.get_current().domain, post.id)

            response_xml = '''<xml>
                             <ToUserName><![CDATA[%(ToUserName)s]]></ToUserName>
                             <FromUserName><![CDATA[%(FromUserName)s]]></FromUserName>
                             <CreateTime>%(CreateTime)s</CreateTime>
                             <MsgType><![CDATA[news]]></MsgType>
                             <ArticleCount>1</ArticleCount>
                             <Articles>
                             <item>
                             <Title><![CDATA[%(Title)s]]></Title> 
                             <Description><![CDATA[%(Description)s]]></Description>
                             <PicUrl><![CDATA[%(PicUrl)s]]></PicUrl>
                             <Url><![CDATA[%(Url)s]]></Url>
                             </item>
                             </Articles>
                             <FuncFlag>1</FuncFlag>
                             </xml>''' % response_dict

            return HttpResponse(response_xml, content_type='application/xml')

    if response_xml:
        return HttpResponse(response_xml, content_type='application/xml')
    else:
        return HttpResponse('Hello World!')
