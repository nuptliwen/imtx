#!/home/tualatrix/public_html/imtx.me/bin/python
import os
import sys

sys.path.append('/home/tualatrix/public_html/imtx.me/imtx')
os.environ['DJANGO_SETTINGS_MODULE'] = 'imtx.settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
