# Build script for TeMMPo - set up to suit the development environment setup.

# Assumes the following:
# pip and virtualenv are installed
# Plus makes use of system installed lxml (/usr/lib/python2.7/dist-packages/lxml)
# Tested with Python 2.7

# Replace file system paths
# Accept argument for virtualenv - defaults to beta
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

# DB
echo "Creating database"
cd $BASEPATH
cd $VE
cd src/temmpo
pwd
../../bin/python manage.py migrate

# Create a super user
echo "Create superuser"
../../bin/python manage.py createsuperuser --settings=temmpo.settings.dev