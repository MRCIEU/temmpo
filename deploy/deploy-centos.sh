#!/bin/sh

# TODO test Apache builds in Travis CI/CD build pipelines as well

echo "###   Build script for a development TeMMPo environment on Centos"
timedatectl set-timezone Europe/London

echo "###   Install EPEL repo and run package updates"
yum -y install epel-release
yum -y update

echo "### Install EPEL package repo"
yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-7.noarch.rpm

echo "Install Centos dev tools, like audit2allow"
yum -y install policycoreutils-python
yum -y install mlocate

echo "# Install python 2 components for Fabric usage"
yum -y install python-devel
yum -y install python-pip
yum -y install python-lxml
yum -y install python-magic

echo "###   Install Python 3 and components"
yum -y install python3
yum -y install python3-setuptools
yum -y install python3-devel
yum -y install python3-pip
yum -y install python3-magic
yum -y install python3-virtualenv
yum -y install python3-lxml

echo "###   Install gcc"
yum -y install gcc gcc-c++

echo "###   Install dev tools"
yum -y install git
yum -y install nano
yum -y install wget
yum -y install mariadb # Database client - adds mysql alias to command line
yum -y install unzip
yum -y install mariadb-devel

echo "###   Setup Web server components"
yum -y install httpd
yum -y install httpd-devel
pip3 install mod-wsgi==4.7.1
usermod -a -G apache vagrant

echo "###   Install DB connectivity tools"
yum -y install mysql-connector-python
yum -y install mysql-utilities
# Required to connect to DB successfully from web server and be able to send emails
setsebool -P httpd_can_network_connect 1
setsebool -P httpd_can_network_connect_db 1
setsebool -P httpd_can_sendmail 1

echo "###   Install anti-virus tools used with Apache fronted instances"
yum -y install clamav
yum -y install clamd
# ref: https://github.com/vstoykov/django-clamd#configuration
# Installed on prod
yum -y install clamav-data
yum -y install clamav-devel

setsebool -P antivirus_can_scan_system 1
setsebool -P daemons_enable_cluster_mode 1
# Use production config as per puppet config,
# see https://gitlab.isys.bris.ac.uk/research_it/clamav/-/blob/master/files/freshclam.conf
# and https://gitlab.isys.bris.ac.uk/research_it/clamav/-/blob/master/templates/scan.conf.epp
if [ -f /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/freshclam.conf ]
  then
    cp /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/freshclam.conf /etc/
  else
    # apache VMs do not mount local source code
    cp /vagrant/deploy/freshclam.conf /etc/
fi
if [ -f /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/scan.conf ]
  then
    cp /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/scan.conf /etc/clamd.d/
  else
    # apache VMs do not mount local source code
    cp /vagrant/deploy/scan.conf /etc/clamd.d/
fi

touch /var/log/clamd.scan
chown clamscan:clamscan /var/log/clamd.scan
usermod -a -G clamscan apache
usermod -a -G virusgroup apache
usermod -a -G clamscan vagrant
usermod -a -G virusgroup vagrant

systemctl start clamd@scan
systemctl enable clamd@scan

# Update virus DB
/bin/freshclam

echo "###   Install fabric (for deployment scripts) and other production Python 2 eggs"
if [ -f /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/pip-freeze-2020-11-23.txt ]
  then
    pip install -r /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/pip-freeze-2020-11-23.txt
  else
    pip install -r /vagrant/deploy/pip-freeze-2020-11-23.txt
fi

echo "###   Install redis"
yum -y install redis
sed -i s'/appendonly no/appendonly yes/' /etc/redis.conf
systemctl start redis.service
systemctl enable redis
# Test redis
redis-cli ping

echo "###   Step up django-rq services"
# TMMA-382: Review and increase number of workers for matching code
for i in 1 2 3 4
do
  cat > /etc/systemd/system/rqworker$i.service <<MESSAGE_QUEUE_WORKER
  [Unit]
  Description=TeMMPo Django-RQ Worker $i
  After=network.target

  [Service]
  User=apache
  Group=vagrant
  WorkingDirectory=/usr/local/projects/temmpo/lib/dev/src/temmpo
  ExecStart=/usr/local/projects/temmpo/lib/dev/bin/python /usr/local/projects/temmpo/lib/dev/src/temmpo/manage.py rqworker default --settings=temmpo.settings.dev --name $i

  [Install]
  WantedBy=multi-user.target
MESSAGE_QUEUE_WORKER

  systemctl enable rqworker$i
  systemctl start rqworker$1
done

echo "###   Install components for Selenium testing"
yum -y install Xvfb
# Install Chrome and chromedriver
cd /tmp
wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
yum -y localinstall google-chrome-stable_current_x86_64.rpm
google-chrome --version
# As per test server
wget https://chromedriver.storage.googleapis.com/2.35/chromedriver_linux64.zip
# wget https://chromedriver.storage.googleapis.com/75.0.3770.8/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
mv chromedriver /usr/bin/
chmod g+rw /usr/bin/chromedriver
chmod o+rw /usr/bin/chromedriver
chromedriver -v

echo "###   Confirm install list"
yum list installed 
pip freeze
pip3 freeze

echo "###   Create directories normally managed by Puppet"
mkdir -p /usr/local/projects/temmpo/etc/apache/conf.d
mkdir -p /usr/local/projects/temmpo/etc/ssl
mkdir -p /usr/local/projects/temmpo/lib/
mkdir -p /usr/local/projects/temmpo/var/log/httpd
mkdir -p /usr/local/projects/temmpo/var/www
mkdir -p /usr/local/projects/temmpo/var/data
mkdir -p /usr/local/projects/temmpo/var/abstracts
mkdir -p /usr/local/projects/temmpo/var/results/v1
mkdir -p /usr/local/projects/temmpo/var/results/v3
mkdir -p /usr/local/projects/temmpo/var/results/v4
mkdir -p /usr/local/projects/temmpo/var/results/testing/v1
mkdir -p /usr/local/projects/temmpo/var/results/testing/v3
mkdir -p /usr/local/projects/temmpo/var/results/testing/v4

echo "###   Add directory for development emails"
mkdir -p /usr/local/projects/temmpo/var/email

touch /usr/local/projects/temmpo/var/log/django.log

chown vagrant:vagrant /usr/local/projects/temmpo/
chown --silent -R vagrant:vagrant /usr/local/projects/temmpo/lib/
chown apache:vagrant /usr/local/projects/temmpo/etc/apache/conf.d
chown -R vagrant:vagrant /usr/local/projects/temmpo/var
chown apache:vagrant /usr/local/projects/temmpo/var/abstracts
chown apache:vagrant /usr/local/projects/temmpo/var/data
chown apache:vagrant /usr/local/projects/temmpo/var/results
chown apache:vagrant /usr/local/projects/temmpo/var/email
chown apache:vagrant /usr/local/projects/temmpo/var/www
chown apache:vagrant /usr/local/projects/temmpo/var/log/django.log
chmod -R g+xw /usr/local/projects/temmpo/var/log
chmod -R g+xw /usr/local/projects/temmpo/var/data
chmod -R g+xw /usr/local/projects/temmpo/var/abstracts
chmod -R g+xw /usr/local/projects/temmpo/var/results
chmod -R g+xw /usr/local/projects/temmpo/var/email
chmod g+xw /usr/local/projects/temmpo/var/www
chmod g+xw /usr/local/projects/temmpo/etc/apache/conf.d
chcon -R -t httpd_config_t /usr/local/projects/temmpo/etc/apache/conf.d
chcon -R -t httpd_sys_rw_content_t /usr/local/projects/temmpo/var

if [ -d "/home/vagrant/.ssh/" ]; then

  echo "###   Copy a deployment key to allow fabric script testing"
  if [ -f /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/id_rsa ]
    then
      cp /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/id_rsa* /home/vagrant/.ssh/
    else
      # apache VMs do not mount local source code
      cp /vagrant/deploy/id_rsa* /home/vagrant/.ssh/
  fi

  ssh-keyscan -H 104.192.143.1 >> /home/vagrant/.ssh/known_hosts
  ssh-keyscan -H 104.192.143.2 >> /home/vagrant/.ssh/known_hosts
  ssh-keyscan -H 104.192.143.3 >> /home/vagrant/.ssh/known_hosts
  ssh-keyscan -H bitbucket.org >> /home/vagrant/.ssh/known_hosts
  ssh-keyscan -H github.com >> /home/vagrant/.ssh/known_hosts

  chown -R vagrant:vagrant /home/vagrant/.ssh/
  chmod 700 /home/vagrant/.ssh/*

fi

echo "###   Add basic catch all Apache config normally managed by Puppet"
cat > /etc/httpd/conf.d/temmpo.conf <<APACHE_CONF
LoadModule wsgi_module "/usr/local/lib64/python3.6/site-packages/mod_wsgi/server/mod_wsgi-py36.cpython-36m-x86_64-linux-gnu.so"
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

echo "###   Add placeholder private_settings.py"
mkdir -p /usr/local/projects/temmpo/.settings/
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
DATABASES['default'] = DATABASES['mysql']
PRIVATE_SETTINGS
chown -R vagrant:vagrant /usr/local/projects/temmpo/.settings/
chmod -R ug+rwx /usr/local/projects/temmpo/.settings/

# Update locate DB
updatedb
echo "###   See README.md for ways to create virtual environments"
