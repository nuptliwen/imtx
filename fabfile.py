from __future__ import with_statement
import os
import sys
import glob
from fabric.api import *
from fabric.contrib.console import confirm

env.user = os.getenv('IMTX_USER')
env.hosts = [os.getenv('IMTX_HOST')]

def createdb(password, database):
    local('mysql -uroot -p%s -e "create database %s"' % (password, database))

def dropdb(password, database):
    local('mysql -uroot -p%s -e "drop database %s"' % (password, database))

def sync():
    tar_list = glob.glob(os.path.expanduser('~/Dropbox/imtx-backup/*.tar.gz'))

    tar_list.sort()
    tar = tar_list[-1]

    local('cd .. && tar zxf %s imtx/imtx/static/' % tar, capture=False)
    local('cd .. && tar zxf %s imtx/imtx/media/' % tar, capture=False)
    local('cd .. && tar zxf %s imtx/imtx/local_settings.py' % tar, capture=False)

    sys.path.insert(0, os.getcwd())
    import imtx.settings

    password = imtx.settings.DATABASES['default']['PASSWORD']
    database = imtx.settings.DATABASES['default']['NAME']

    if password and database:
        try:
            dropdb(password, database)
        except:
            pass
        createdb(password, database)

    if os.uname()[0] == 'Darwin':
        local("gsed -i 's/DEBUG = False/DEBUG = True/g' imtx/local_settings.py", capture=False)
    else:
        local("sed -i 's/DEBUG = False/DEBUG = True/g' imtx/local_settings.py", capture=False)

    sql_list = glob.glob(os.path.expanduser('~/Dropbox/imtx-backup/*.sql.gz'))

    sql_list.sort()
    sql = sql_list[-1]
    base_name = os.path.basename(sql)
    local('rm -rf /tmp/imtx*')
    local('cp %s /tmp/%s' % (sql, base_name))
    local('gunzip /tmp/%s' % base_name)
    local('mysql -uroot -p%s %s < /tmp/%s' % (password, database, base_name[:-3]))
    local('rm /tmp/%s' % base_name[:-3])
    local("""echo 'EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"\nCACHES = {"default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}}' >> imtx/local_settings.py""", capture=False)

def install():
    local('pip install -r requirements.txt', capture=False)

def runserver():
    local('python manage.py runserver', capture=False)

def deploy(pip='no', restart='no', static='no'):
    with cd('~/public_html/imtx.me/imtx'):
        run('git pull origin master')
        if pip != 'no':
            run('/home/tualatrix/public_html/imtx.me/bin/pip install -r requirements.txt')
            run('sudo service uwsgi restart')
        if restart != 'no':
            run('sudo service uwsgi restart')
        if static != 'no':
            run('/home/tualatrix/public_html/imtx.me/bin/python /home/tualatrix/public_html/imtx.me/imtx/manage.py collectstatic --noinput')

def migrate():
    with cd('~/public_html/imtx.me/imtx/imtx'):
        run('/home/tualatrix/public_html/imtx.me/bin/python manage.py migrate')
        run('touch django.wsgi')

def shell():
    with cd('imtx'):
        local('python manage.py shell', capture=False)
