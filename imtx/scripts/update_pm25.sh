#!/bin/bash

cd /home/tualatrix/public_html/imtx.me/imtx
workon imtx.me
/home/tualatrix/public_html/imtx.me/bin/python manage.py update_pm25
