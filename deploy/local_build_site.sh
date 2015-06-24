# Build script for TeMMPo
# Accept argument for VE - defaults to beta
# Accept argument for git user - defaults to beta
# Requires Python 2.7 and virtualenv
MY_USER=$(whoami)
VE="beta"
BASEPATH=$(pwd)

# Allow override of virtual environment name
if [ -n "$1" ]; then
    VE=$1
    echo "Overriding the default virtual environment name with:"
    echo $VE
fi

# Allow override of git username
if [ -n "$2" ]; then
    MY_USER=$2
    echo "Overriding the git username with:"
    echo $MY_USER
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
git clone "$MY_USER"@git.ilrt.bris.ac.uk:/usr/local/projects/git/projects/temmpo

# Load requirements
echo "Load requirements"
cd $BASEPATH
cd $VE
cd src/temmpo
pwd
../../bin/pip install -r deploy/project-eggs-freeze.txt

# DB
echo "Creating SQLite db"
../../bin/python manage.py migrate

# Create a super user
echo "Create superuser"
../../bin/python manage.py createsuperuser --settings=temmpo.settings.dev