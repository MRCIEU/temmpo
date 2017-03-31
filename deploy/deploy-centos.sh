	echo "Build script for TeMMPo"

sudo yum -y install epel-release
sudo yum -y update
sudo yum -y install python-devel
sudo yum -y install python-wheel
sudo yum -y install python-magic
sudo yum -y install python-pip
sudo yum -y install python-virtualenv
sudo yum -y install libxml2-python
sudo yum -y install libxml2-devel
sudo yum -y install libxslt-python
sudo yum -y install libxslt-devel
sudo yum -y install python-lxml

# install fabric for deployment scripts
sudo pip install fabric==1.13.1

# install gcc
sudo yum -y install gcc gcc-c++

# dev tools
sudo yum -y install git
sudo yum -y install nano
sudo yum -y install wget
# mariadb dev stuff
sudo yum -y install mariadb-devel

# Web server setup
sudo yum -y install httpd 
sudo yum -y install mod_wsgi

# Confirm install list
yum list installed 

echo "Create directories normally managed by Puppet"
mkdir -p /usr/local/projects/temmpo/lib/
mkdir -p /usr/local/projects/temmpo/etc/apache/conf.d
mkdir -p /usr/local/projects/temmpo/etc/ssl
mkdir -p /usr/local/projects/temmpo/var/log/httpd
mkdir -p /usr/local/projects/temmpo/var/www

echo "TODO: add basic Apache config normally managed by Puppet"
cd /usr/local/projects/temmpo/lib/
chown --silent -R vagrant:vagrant dev


echo "## How to create/update the database"
echo "cd /srv/projects/temmpo/lib/dev/src/temmpo"
echo "../../bin/python manage.py migrate --settings=temmpo.settings.dev"

echo "## How to run the test suite"
echo "cd /usr/local/projects/temmpo/lib/dev/src/temmpo && ../../bin/python manage.py test --settings=temmpo.settings.dev"

echo "## Populate with all the mesh terms (NB: This takes a very long time - alternatively load test fixtures mesh-terms-test-only.json)"
echo "cd /usr/local/projects/temmpo/lib/dev/src/temmpo && ../../bin/python manage.py import_mesh_terms"

echo "## Populate with the full genes list (NB: This takes a very long time - alternatively load test fixtures genes-test-only.json)"
echo "cd /usr/local/projects/temmpo/lib/dev/src/temmpo && ../../bin/python manage.py import_genes"

echo "## How to create superuser"
echo "cd /usr/local/projects/temmpo/lib/dev/src/temmpo && ../../bin/python manage.py createsuperuser --settings=temmpo.settings.dev"

echo "## How to run the dev server"
echo "cd /usr/local/projects/temmpo/lib/dev/src/temmpo && ../../bin/python manage.py runserver 0.0.0.0:59099 --settings=temmpo.settings.dev"
echo "## Open http://127.0.0.1:59099 in your web browser"
