# Build script for TeMMPo when working with Apache
# Tested with Django 1.7.4
# Accept argument for name of environment, i.e. dev or prod 
# Assumes there will be a matching settings file and requirements text file

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
mkdir static
mkdir var
mkdir var/results

# Clone git repo
echo "Clone repo"
cd src
pwd
git clone git@bitbucket.org:researchit/temmpo.git

# Sym link in core libraries - in particular any that require compilation
cd $BASEPATH
cd $VE
cd ./lib/python2.7/site-packages/
pwd
ln -s /usr/lib/python2.7/dist-packages/lxml lxml
ln -s /usr/lib/python2.7/dist-packages/lxml-2.3.2.egg-info lxml-2.3.2.egg-info

# Load requirements
echo "Load requirements"
cd $BASEPATH
cd $VE
cd src/temmpo
pwd
../../bin/pip install -r requirements/base.txt
../../bin/pip install -r requirements/$VE.txt

# Set up Apache stuff 
echo "TODO: Append settings location to the end of the django admin file"
# django-admin.py and mod_wsgi file

# Append to end of django-admin.py
# < import os, sys
# < sys.path.append('/usr/local/projects/tmma/lib/prod/src/temmpo/')
# < os.environ["DJANGO_SETTINGS_MODULE"] = "temmpo.settings.prod"

echo "TODO: Now create a WSGI file"
# TODO automate this step.
# echo "Create WSGI file"
# Create config file /usr/local/projects/tmma/apache/conf/conf.d/00_wsgi.conf

# WSGIScriptAlias / /usr/local/projects/tmma/lib/prod/bin/django.wsgi

# # performance set keep alive off and no handler on direct static files 
# KeepAlive Off
# WSGIApplicationGroup tmma

# Alias /static "/usr/local/projects/tmma/lib/prod/static"
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
