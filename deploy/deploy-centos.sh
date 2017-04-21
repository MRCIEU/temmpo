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
sudo yum -y install mysql # TODO add to puppet
# 
sudo yum -y install mariadb-devel

# Web server setup
sudo yum -y install httpd 
sudo yum -y install mod_wsgi

# DB connectivity tools
sudo yum -y install mysql-connector-python
sudo yum -y install mysql-utilities

# Production tools
sudo yum -y install clamav

# install fabric for deployment scripts
sudo pip install fabric==1.13.1

# sudo pip install pip==9.0.1

# Confirm install list
yum list installed 
pip freeze

echo "Create directories normally managed by Puppet"
mkdir -p /usr/local/projects/temmpo/etc/apache/conf.d
mkdir -p /usr/local/projects/temmpo/etc/ssl
mkdir -p /usr/local/projects/temmpo/lib/
mkdir -p /usr/local/projects/temmpo/var/log/httpd
mkdir -p /usr/local/projects/temmpo/var/www
mkdir -p /usr/local/projects/temmpo/var/data
mkdir -p /usr/local/projects/temmpo/var/abstracts
mkdir -p /usr/local/projects/temmpo/var/results

touch /usr/local/projects/temmpo/var/log/django.log

sudo chown --silent -R vagrant:vagrant /usr/local/projects/temmpo/lib/
sudo chown apache:vagrant /usr/local/projects/temmpo/etc/apache/conf.d
sudo chown -R vagrant:vagrant /usr/local/projects/temmpo/var
sudo chown apache:vagrant /usr/local/projects/temmpo/var/abstracts
sudo chown apache:vagrant /usr/local/projects/temmpo/var/data
sudo chown apache:vagrant /usr/local/projects/temmpo/var/results
sudo chown apache:vagrant /usr/local/projects/temmpo/var/www
sudo chown apache:vagrant /usr/local/projects/temmpo/var/log/django.log
sudo chmod -R g+xw /usr/local/projects/temmpo/var/log
sudo chmod -R g+xw /usr/local/projects/temmpo/var/data
sudo chmod -R g+xw /usr/local/projects/temmpo/var/abstracts
sudo chmod -R g+xw /usr/local/projects/temmpo/var/results
sudo chmod g+xw /usr/local/projects/temmpo/var/www
sudo chmod g+xw /usr/local/projects/temmpo/etc/apache/conf.d
sudo chcon -R -t httpd_config_t /usr/local/projects/temmpo/etc/apache/conf.d
sudo chcon -R -t httpd_sys_rw_content_t /usr/local/projects/temmpo/var

echo "Copy a deployment key to allow fabric script testing"
if [ -f /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/id_rsa ]
  then
    cp /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/id_rsa* /home/vagrant/.ssh/
  else
    cp /vagrant/deploy/id_rsa* /home/vagrant/.ssh/
fi

ssh-keyscan -H 104.192.143.1 >> /home/vagrant/.ssh/known_hosts
ssh-keyscan -H 104.192.143.2 >> /home/vagrant/.ssh/known_hosts
ssh-keyscan -H 104.192.143.3 >> /home/vagrant/.ssh/known_hosts
ssh-keyscan -H bitbucket.org >> /home/vagrant/.ssh/known_hosts

sudo chown -R vagrant:vagrant /home/vagrant/.ssh/
sudo chmod 700 /home/vagrant/.ssh/*

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

echo "Add placeholder private_settings.py"
sudo mkdir -p /usr/local/projects/temmpo/.settings/
cat > /usr/local/projects/temmpo/.settings/private_settings.py <<PRIVATE_SETTINGS
DATABASES = {
    'mysql': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'temmpo_d',
        'USER': 'temmpo',
        'PASSWORD': 'notsosecret',
        'HOST': '192.168.50.70',
        'PORT': '3306',
        'OPTIONS': {
            'sql_mode': 'STRICT_ALL_TABLES'
        }
    },
    'admin': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'temmpo_d',
        'USER': 'temmpo_a',
        'PASSWORD': 'notsosecret_a',
        'HOST': '192.168.50.70',
        'PORT': '3306',
        'OPTIONS': {
            'sql_mode': 'STRICT_ALL_TABLES'
        }
    },
    'sqlite': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/usr/local/projects/temmpo/var/data/db.sqlite3',
    },
}

# Prepare for database migration
DATABASES['default'] = DATABASES['sqlite']
PRIVATE_SETTINGS
sudo chown -R vagrant:vagrant /usr/local/projects/temmpo/.settings/
sudo chmod -R ug+rwx /usr/local/projects/temmpo/.settings/

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
