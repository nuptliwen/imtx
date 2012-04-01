#coding: utf-8
import sys
reload(sys)
import os
import time
sys.setdefaultencoding('utf8')

from django.core.management.base import BaseCommand, CommandError
from imtx.views import get_pm25_dict

class Command(BaseCommand):
    def handle(self, *args, **options):
        pmdata = get_pm25_dict()

        if os.path.exists('timestamp'):
            timestamp = open('timestamp').read().strip()
        else:
            timestamp = ''

        if timestamp != pmdata['date']:
            for city, data in pmdata['cities'].items():
                message = u'【%s %s空气质量】' % (pmdata['date'], city) + u'PM2.5浓度: %(concentration)s ug/m3, AQI: %(aqi)s, 等级: %(category)s' % data
                print message
                os.system(u'twitter set "%s"' % message)
                time.sleep(3)

            f = open('timestamp', 'w')
            f.write(pmdata['date'])
            f.close()
        else:
            print 'No update yet'
