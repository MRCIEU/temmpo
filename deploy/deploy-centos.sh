echo "Build script for TeMMPo"
sudo timedatectl set-timezone Europe/London
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

# install fabric for deployment scripts
sudo pip install fabric==1.13.1

# Confirm install list
yum list installed 
pip freeze

echo "Create directories normally managed by Puppet"
mkdir -p /usr/local/projects/temmpo/lib/
mkdir -p /usr/local/projects/temmpo/etc/apache/conf.d
mkdir -p /usr/local/projects/temmpo/etc/ssl
mkdir -p /usr/local/projects/temmpo/var/log/httpd
mkdir -p /usr/local/projects/temmpo/var/www
mkdir -p /usr/local/projects/temmpo/var/data

echo "Add basic catch all Apache config normally managed by Puppet"
cat > /etc/httpd/conf.d/temmpo.conf <<APACHE_CONF
WSGIPythonHome "/usr/local/projects/temmpo/lib/dev"

<VirtualHost *:*>
  ServerName www.temmpo.org.uk
  ServerAlias temmpo.org.uk
  ServerAlias dev.temmpo.org.uk
  ServerAlias vagrant.temmpo.org.uk

  ## Vhost docroot
  DocumentRoot "/usr/local/projects/temmpo/var/www"

  ## Directories, there should at least be a declaration for /usr/local/projects/temmpo/var/www

  <Directory "/usr/local/projects/temmpo/var/www">
    Options Indexes FollowSymLinks MultiViews
    AllowOverride None
    Require all granted
  </Directory>

  ## Load additional static includes
  IncludeOptional "/usr/local/projects/temmpo/etc/apache/conf.d/*.conf"
</VirtualHost>
APACHE_CONF

cd /usr/local/projects/temmpo/lib/
sudo chown --silent -R vagrant:vagrant /usr/local/projects/temmpo/lib/
sudo chown vagrant:apache /usr/local/projects/temmpo/etc/apache/conf.d
sudo chown -R vagrant:apache /usr/local/projects/temmpo/var
sudo chmod -R g+w /usr/local/projects/temmpo/var/log
sudo chcon -R -t httpd_config_t /usr/local/projects/temmpo/etc/apache/conf.d
sudo chcon -R -t httpd_sys_rw_content_t /usr/local/projects/temmpo/var

echo "Copy a deployment key to allow fabric script testing"
cp /vagrant/deploy/id_rsa* /home/vagrant/.ssh/
sudo chown -R vagrant:vagrant /home/vagrant/.ssh/
sudo chmod 700 /home/vagrant/.ssh/*

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
