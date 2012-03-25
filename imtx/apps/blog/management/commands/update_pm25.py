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
        for city, data in pmdata['cities'].items():
            message = u'【%s %s空气质量】' % (pmdata['date'], city) + u'PM2.5浓度: %(concentration)s ug/m3, AQI: %(aqi)s, 等级: %(category)s' % data
            os.system(u'twitter set "%s"' % message)
            time.sleep(3)
