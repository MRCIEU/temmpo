# Build script for TeMMPo
BASEPATH="/usr/local/projects/tmma/lib/dev"

if [ ! -d "$BASEPATH" ]; then
  echo "Environment does not exist"
  echo $BASEPATH
  exit
fi

cd $BASEPATH
pwd

echo "Create required sub directories, where required"
mkdir -p etc
mkdir -p share
mkdir -p src
mkdir -p var

# Clone git repo
# TODO - pull a particular branch?
echo "Update code repo"
cd src/temmpo
git pull

# Sym link in core libraries - in particular any that require compilation
cd $BASEPATH
cd ./lib/python2.7/site-packages/
pwd
ln -s /usr/lib/python2.7/dist-packages/lxml lxml
ln -s /usr/lib/python2.7/dist-packages/lxml-2.3.2.egg-info lxml-2.3.2.egg-info

# TODO consider using linking to core version of Django on the VM

# Load requirements
echo "Install any new or updated eggs"
cd $BASEPATH
cd src/temmpo
pwd
../../bin/pip install -r deploy/project-eggs-freeze.txt
../../bin/pip install -r deploy/now.txt

# DB
echo "Update database with any new migrations"
cd $BASEPATH
cd src/temmpo
pwd
../../bin/python manage.py migrate

echo "Set expected custom permissions"
cd $BASEPATH
sudo /usr/local/bin/reset-perms -w var

cd src
sudo /usr/local/bin/reset-perms -u temmpo
sudo chown www-data temmpo/temmpo
sudo chown www-data temmpo/temmpo/db.sqlite3

echo "You may now wish to load the fixture data: genes.json and mesh-terms.json"