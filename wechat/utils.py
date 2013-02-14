# coding: utf-8

import re
import json
import random
import datetime

from lxml import etree
from django.http import HttpResponse
from django.db.models import Q
from django.contrib.sites.models import Site

from imtx.apps.blog.models import Post
from imtx.views import aqi_pm25, aqi_category
from wechat.models import WechatUser, Article, MessageResponse

def etree_to_dict(t):
    d = {}
    for t in t.iterchildren():
        d[t.tag] = t.text
    return d

def process_request(request):
    response_xml = ''
    request_dict = etree_to_dict(etree.fromstring(request.raw_post_data))
    # If has no content, save the whole dict to be future process
    request_content = request_dict.get('Content', json.dumps(request_dict))

    user, created = WechatUser.objects.get_or_create(name=request_dict['FromUserName'])
    message_response = MessageResponse.objects.create(user=user,
                                                      request_content=request_content)
    if request_content == 'Hello2BizUser':
        message_response.message_type = 'hello'
        message_response.response_content = u'Hello, 我是TualatriX! 感谢关注IMTX，你可以通过发送「top」（不区分大小写）来查看最新三篇文章，或者搜索关键字来随机查看我过去写的文章，尝试一下？如: Python。'
        message_response.save()

        response_xml = message_response.build_response_xml()
    elif request_content.isdigit():
        pm25 = int(request_content)
        message_response.response_content = u'AQI: %s, %s' % (aqi_pm25(pm25), aqi_category(aqi_pm25(pm25)))
        message_response.save()

        response_xml = message_response.build_response_xml()
    elif request_content.lower() == 'top':
        posts = Post.objects.get_post()[:3]
        if posts:
            message_response.create_articles_from_posts(posts)
            response_xml = message_response.build_response_xml()
    elif request_content:
        qset = (Q(title__icontains=request_content) | Q(title__icontains=request_content))
        posts = Post.objects.filter(qset, status='publish').distinct()

        if posts:
            post_count = posts.count()

            if post_count > 3:
                post_ids = random.sample(range(post_count), 3)
                new_posts = []
                for id in post_ids:
                    new_posts.append(posts[id])
                posts = new_posts

            message_response.create_articles_from_posts(posts)
            response_xml = message_response.build_response_xml()
    else:
        message_response.save()

    if response_xml:
        return HttpResponse(response_xml, content_type='application/xml')
    else:
        return HttpResponse('Hello World!')
