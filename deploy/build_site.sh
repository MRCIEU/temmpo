# Build script for TeMMPo
# Accept argument for VE - defaults to beta
MY_USER=$(whoami)
BASEPATH="/usr/local/projects/tmma/lib/"$MY_USER
VE="beta"

if [ ! -d "$BASEPATH" ]; then
  echo "Create directory"
  mkdir $BASEPATH
else
  echo "Directory exists"
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

#bin/pip install django # Tested with 1.7.4
#bin/pip install django-chunked-upload # Trialing
#bin/pip install django-bft # Trialing
#bin/pip install recaptcha-client

# DB
echo "Creating SQLite db"
cd $BASEPATH
cd $VE
cd src/temmpo
pwd
../../bin/python manage.py migrate

# Create a super user
echo "Create superuser"
../../bin/python manage.py createsuperuser --settings=temmpo.settings.dev