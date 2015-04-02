# Build script for TeMMPo
# Accept argument for name of environment, i.e. dev, demo or prod should have matching settings file
BASEPATH="/usr/local/projects/tmma/lib/"
VE="prod"

if [ ! -d "$BASEPATH" ]; then
  echo "Create directory"
  mkdir $BASEPATH
else
  echo "Directory exists"
  echo $BASEPATH
fi

cd $BASEPATH
pwd

# Allow override of virtual environment name
if [ -n "$1" ]; then
    VE=$1
    echo "Overriding the default virtual environment name with:"
    echo $VE
fi

echo "Create virtual environment in this location:"
pwd
virtualenv --no-site-packages $VE
cd $VE
pwd
echo "Create required sub directories"
mkdir etc
mkdir share
mkdir src
mkdir var

# Clone git repo
echo "Clone repo"
cd src
pwd
git clone git.ilrt.bris.ac.uk:/usr/local/projects/git/projects/temmpo

# Sym link in core libraries - in particular any that require compilation
cd $BASEPATH
cd $VE
cd ./lib/python2.7/site-packages/
pwd
ln -s /usr/lib/python2.7/dist-packages/lxml lxml
ln -s /usr/lib/python2.7/dist-packages/lxml-2.3.2.egg-info lxml-2.3.2.egg-info

# TODO consider using core version of Django on the box

# Load requirements
echo "Load requirements"
cd $BASEPATH
cd $VE
cd src/temmpo
pwd
../../bin/pip install -r deploy/project-eggs-freeze.txt
../../bin/pip install -r deploy/now.txt

#bin/pip install django # Tested with 1.7.4
#bin/pip install django-chunked-upload # Trialing
#bin/pip install django-bft # Trialing
#bin/pip install recaptcha-client

# TODO set up Apache stuff 
echo "Append to django admin file"
# django-admin.py and mod_wsgi file

# Append to end of django-admin.py
# < import os, sys
# < sys.path.append('/usr/local/projects/tmma/lib/prod/src/temmpo/')
# < os.environ["DJANGO_SETTINGS_MODULE"] = "temmpo.settings.prod"

echo "TODO: Create wsgi file"
echo "What about django.wsgi"
# echo "Create WSGI file"
# Create config file /usr/local/projects/tmma/apache/conf/conf.d/00_wsgi.conf

# WSGIScriptAlias / /usr/local/projects/tmma/lib/prod/bin/django.wsgi

# # performance set keep alive off and no handler on direct static files 
# KeepAlive Off
# WSGIApplicationGroup tmma

# Alias /static "/usr/local/projects/tmma/lib/prod/src/temmpo/browser/static"
# <Location "/static">
#     SetHandler None
# </Location>

# <Directory /usr/local/projects/tmma/lib/prod/src/temmpo/temmpo>
# <Files wsgi.py>
# Order deny,allow
# Allow from all
# </Files>
# </Directory>

# DB
echo "Creating SQLite db"
cd $BASEPATH
cd $VE
cd src/temmpo
pwd
../../bin/python manage.py migrate

# Create a super user
echo "Create superuser"
../../bin/python manage.py createsuperuser --settings=temmpo.settings.$VE

