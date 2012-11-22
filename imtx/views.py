#coding: utf-8
import urllib
from collections import OrderedDict

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils import simplejson

from BeautifulSoup import BeautifulSoup

from paypal.standard.forms import PayPalPaymentsForm

def purchase(request):
    # What you want the button to do.
    paypal_dict = {
        "business": "tualat_1353483092_biz@gmail.com",
        "amount": "5.00",
        "item_name": "Manity License",
        "invoice": "me.imtx.manity.license",
        "notify_url": request.build_absolute_uri('/paypal/pdt/'),
        "return_url": request.build_absolute_uri('/paypal/pdt/'),
        "cancel_return": request.build_absolute_uri('/paypal/pdt/'),
    }

    # Create the instance.
    form = PayPalPaymentsForm(initial=paypal_dict)
    context = {"form": form}
    return render_to_response("payment.html", context)

def linear(aqi_high, aqi_low, conc_high, conc_low, conc):
    a = ((conc - conc_low) / (conc_high - conc_low)) * (aqi_high - aqi_low) + aqi_low
    return int(round(a))

def aqi_pm25(c):
    if c >= 0 and c < 15.5:
        return linear(50, 0, 15.4, 0, c)
    elif c >= 15.5 and c < 35.5:
        return linear(100, 51, 35.4, 15.5, c)
    elif c >= 35.5 and c < 65.5:
        return linear(150, 101, 65.4, 35.5, c)
    elif c >= 65.5 and c < 150.5:
        return linear(200, 151, 150.4, 65.5, c)
    elif c >= 150.5 and c < 250.5:
        return linear(300, 201, 250.4, 150.5, c)
    elif c >= 250.5 and c < 350.5:
        return linear(400, 301, 350.4, 250.5, c)
    elif c >= 350.5 and c < 500.5:
        return linear(500,401,500.4,350.5, c)
    else:
        return "Out of Range"

def aqi_category(aqi):
    if aqi <= 50:
        return u"优良"
    elif aqi > 50 and aqi <= 100:
        return u"中等"
    elif aqi > 100 and aqi <= 150:
        return u"敏感群体有害"
    elif aqi > 150 and aqi <= 200:
        return u"不健康"
    elif aqi > 200 and aqi <= 300:
        return u"非常不健康"
    elif aqi > 300 and aqi <= 400:
        return u"有毒害一级"
    elif aqi > 400 and aqi <= 500:
        return u"有毒害二级"
    else:
        return u"尼玛！PM2.5爆表啦！"

def get_pm25_dict():
    data = {}
    content = urllib.urlopen('http://app.zjepb.gov.cn:8080/wasdemo/search?channelid=121215').read()

    soup = BeautifulSoup(content)
    data['date'] = soup.find(id='1')['value']
    data['cities'] = OrderedDict()

    for td in soup.findAll(height='23'):
        tr = td.parent

        city = tr.findChild().text
        concentration = int(tr.findChildren()[3].text)
        aqi = aqi_pm25(concentration)
        category = aqi_category(aqi)
        data['cities'][city] = {'concentration': concentration,
                      'aqi': aqi,
                      'category': category}
    return data

def zhejiangpm25(request):
    response = simplejson.dumps(get_pm25_dict())
    return HttpResponse(response, mimetype="application/json")
