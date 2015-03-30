# Build script for TeMMPo
MY_USER=$(whoami)
BASEPATH="/usr/local/projects/tmma/lib/"$MY_USER
if [[ ! -d "$BASEPATH" ]]; then
  echo "Create directory"
  mkdir "$BASEPATH"
else
  echo "Directory exists"
fi

cd "$BASE_PATH"

virtualenv --no-site-packages beta
cd beta
mkdir etc
mkdir share
mkdir src
mkdir var

# Clone git repo
echo "Clone repo"
cd src
git clone git.ilrt.bris.ac.uk:/usr/local/projects/git/projects/temmpo

# Load requirements
echo "Load requirements"
../bin/pip install -r temmpo/deploy/project-eggs-freeze.txt
../bin/pip install -r temmpo/deploy/now.txt

#bin/pip install django # Tested with 1.7.4
#bin/pip install django-chunked-upload # Trailing
#bin/pip install django-bft # Trailing
#bin/pip install recaptcha-client

cd ../lib/python2.7/site-packages/
ln -s /usr/lib/python2.7/dist-packages/lxml lxml
ln -s /usr/lib/python2.7/dist-packages/lxml-2.3.2.egg-info lxml-2.3.2.egg-info

# DB
echo "Creating SQLite db"
cd $BASEPATH
cd beta/src/temmpo
../../bin/python manage.py migrate

# Create a super user
echo "Create superuser"
 ../../bin/python manage.py createsuperuser --settings=temmpo.settings.dev

