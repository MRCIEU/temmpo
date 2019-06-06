echo "Build script for a development TeMMPo environment on Centos"
timedatectl set-timezone Europe/London
yum -y install epel-release
yum -y update
yum -y install python-devel
yum -y install python-wheel
yum -y install python-magic
yum -y install python-pip
yum -y install python-virtualenv
yum -y install libxml2-python
yum -y install libxml2-devel
yum -y install libxslt-python
yum -y install libxslt-devel
yum -y install python-lxml

# install gcc
yum -y install gcc gcc-c++

# dev tools
yum -y install git
yum -y install nano
yum -y install wget
yum -y install mariadb # Database client - adds mysql alias to command line
yum -y install unzip

yum -y install mariadb-devel

# Web server setup
yum -y install httpd
yum -y install mod_wsgi

# DB connectivity tools
yum -y install mysql-connector-python
yum -y install mysql-utilities

# Required to connect to DB successfully from web server and be able to send emails
setsebool -P httpd_can_network_connect 1
setsebool -P httpd_can_network_connect_db 1
setsebool -P httpd_can_sendmail 1

# Production tools
yum -y install clamav

# install fabric for deployment scripts
pip install fabric==1.13.1

# Install redis
yum -y install redis

sed -i s'/appendonly no/appendonly yes/' /etc/redis.conf

systemctl start redis.service
systemctl enable redis
redis-cli ping

cat > /etc/systemd/system/rqworker.service <<MESSAGE_QUEUE_WORKER
[Unit]
Description=Django-RQ Worker
After=network.target

[Service]
User=apache
Group=vagrant
WorkingDirectory=/usr/local/projects/temmpo/lib/dev/src/temmpo
ExecStart=/usr/local/projects/temmpo/lib/dev/bin/python /usr/local/projects/temmpo/lib/dev/src/temmpo/manage.py rqworker default --settings=temmpo.settings.dev

[Install]
WantedBy=multi-user.target
MESSAGE_QUEUE_WORKER

systemctl start rqworker
systemctl enable rqworker

# Install components for Selenium testing
yum -y install Xvfb

# Install Chrome and chromedriver
cd /tmp
wget https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm
yum -y localinstall google-chrome-stable_current_x86_64.rpm
google-chrome --version
wget https://chromedriver.storage.googleapis.com/2.35/chromedriver_linux64.zip. # As per test server
# wget https://chromedriver.storage.googleapis.com/75.0.3770.8/chromedriver_linux64.zip
unzip chromedriver_linux64.zip
mv chromedriver /usr/bin/
chmod g+rw /usr/bin/chromedriver
chmod o+rw /usr/bin/chromedriver
chromedriver -v

# # Install Firefox and geckodriver
# yum -y install firefox
# cd /opt
# wget https://github.com/mozilla/geckodriver/releases/download/v0.24.0/geckodriver-v0.24.0-linux64.tar.gz
# tar -xvf geckodriver-v0.24.0-linux64.tar.gz
# ln -s /opt/geckodriver /usr/local/bin/geckodriver
# geckodriver --version

# # Install PhantomJS NB: Deprecated usage with selenium
# cd /opt
# wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-2.1.1-linux-x86_64.tar.bz2
# tar -xvf phantomjs-2.1.1-linux-x86_64.tar.bz2
# ln -s /opt/phantomjs-2.1.1-linux-x86_64/bin/phantomjs /usr/local/bin/phantomjs
# phantomjs --version

# # Install Opera and operadriver
# rpm --import https://rpm.opera.com/rpmrepo.key
# tee /etc/yum.repos.d/opera.repo <<REPO
# [opera]
# name=Opera packages
# type=rpm-md
# baseurl=https://rpm.opera.com/rpm
# gpgcheck=1
# gpgkey=https://rpm.opera.com/rpmrepo.key
# enabled=1
# REPO
# yum -y install opera-stable
# cd /opt
# wget https://github.com/operasoftware/operachromiumdriver/releases/download/v.2.45/operadriver_linux64.zip
# unzip operadriver_linux64.zip
# ls
# ln -s /opt/operadriver_linux64/operadriver /usr/local/bin/operadriver
# operadriver --version

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
mkdir -p /usr/local/projects/temmpo/var/results/v1
mkdir -p /usr/local/projects/temmpo/var/results/v3
mkdir -p /usr/local/projects/temmpo/var/results/testing/v1
mkdir -p /usr/local/projects/temmpo/var/results/testing/v3

echo "Add directory for development emails"
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

  chown -R vagrant:vagrant /home/vagrant/.ssh/
  chmod 700 /home/vagrant/.ssh/*

fi

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

echo "See README.md for ways to create virtual environments"
