#!/home/tualatrix/public_html/imtx.me/bin/python
import os
import sys
import glob
import datetime

sys.path.append('/home/tualatrix/public_html/imtx.me/imtx')
os.environ['DJANGO_SETTINGS_MODULE'] = 'imtx.settings'

import imtx

from imtx.apps.blog.models import Media
from imtx.apps.blog.models import Post

print("Please input the prefix: "),
prefix = raw_input()

to_add =  glob.glob('/home/tualatrix/public_html/imtx.me/imtx/imtx/static/uploads/2011/10/%s*.*' % prefix)
to_add.sort()

html = []
for path in to_add:
    basename = os.path.basename(path)
    m, created = Media.objects.get_or_create(title=basename.split('.')[0], image='uploads/2011/10/%s' % basename)
    m.save()
    html.append('<p><a href="%s"><img src="%s" alt="%s" /></a></p>' % (m.watermarked.url, m.watermarked.url, m.title))

print '\n'.join(html)
