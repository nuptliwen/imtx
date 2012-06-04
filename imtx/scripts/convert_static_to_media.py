#!/home/tualatrix/public_html/imtx.me/bin/python

import os
import sys
import glob
import time
import datetime

project_path = "/".join(os.path.realpath(__file__).split('/')[:-3])
sys.path.append(project_path)
os.environ['DJANGO_SETTINGS_MODULE'] = 'imtx.settings'

import imtx
from imtx.apps.blog.models import Post

for post in Post.objects.all():
    changed = False
    if 'imtx.cn/static/pictures' in post.content:
        changed = True
        post.content = post.content.replace('imtx.cn/static/pictures', 'imtx.me/media/pictures')

    if 'imtx.cn/static/uploads' in post.content:
        changed = True
        post.content = post.content.replace('imtx.cn/static/uploads', 'imtx.me/media/uploads')

    if 'static/pictures' in post.content:
        changed = True
        post.content = post.content.replace('static/pictures', 'media/pictures')

    if 'static/uploads' in post.content:
        changed = True
        post.content = post.content.replace('static/uploads', 'media/uploads')

    if changed:
        print post
        time.sleep(0.1)
        post.save()
