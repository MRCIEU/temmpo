#!/bin/sh

python3 --version
yum repolist enabled

# yum-config-manager --add-repo

echo "###   Build script for a development TeMMPo environment on RHEL"
timedatectl set-timezone Europe/London

subscription-manager repos --enable rhel-8-server-optional-rpms
subscription-manager repos --enable rhel-8-server-extras-rpms
subscription-manager repos --enable codeready-builder-for-rhel-8-x86_64-rpms
subscription-manager repos --enable docker
subscription-manager repos --enable epel
subscription-manager repos --enable mysql-connectors-community
subscription-manager repos --enable mysql-tools-community
subscription-manager repos --enable mysql57-community
subscription-manager repos --enable rhel-8-for-x86_64-appstream-rpms
subscription-manager repos --enable rhel-8-for-x86_64-baseos-rpms

yum repolist enabled

# rhel-8-for-x86_64-appstream-rpms

yum install -y wget
# 8-21.el8
wget -N https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
rpm -ivh --replacepkgs epel-release-latest-8.noarch.rpm

yum -y update

echo "Install Centos dev tools, like audit2allow"
yum -y install policycoreutils-python
yum -y install mlocate

echo "###   Install dev tools"
yum -y install rh-git227
yum -y install nano
yum -y install unzip
yum -y install sqlite-devel

echo "MySQL client stuff"

# Refresh the MySQL GPG keys - important if we want the mysqll client to install properly.
rpm --import https://repo.mysql.com/RPM-GPG-KEY-mysql-2022
# Clean up default mariadb installations
yum -y remove mariadb-libs
yum -y install mysql-devel
wget https://repo.mysql.com/mysql84-community-release-el8-1.noarch.rpm
yum localinstall -y mysql84-community-release-el8-1.noarch.rpm
yum -y install mysql-community-libs
yum -y install mysql-community-client

echo "###   Setup Web server components"
yum -y install httpd
yum -y install httpd-devel
# yum -y install httpd-manual
# Required to connect to DB successfully from web server and be able to send emails
setsebool -P httpd_can_network_connect 1
setsebool -P httpd_can_network_connect_db 1
setsebool -P httpd_can_sendmail 1

echo "###   Install Python 3.12 and components"

yum -y install gcc gcc-c++ openssl-devel bzip2-devel libffi-devel zlib-devel
cd /opt
wget https://www.python.org/ftp/python/3.9.20/Python-3.9.20.tgz
tar -xzf Python-3.9.20.tgz
cd Python-3.9.20/
./configure --enable-optimizations --enable-shared
make altinstall
# Create symlinks
ln -sfn /usr/local/bin/python3.12 /usr/bin/python3.12
ln -sfn /usr/local/bin/pip3.9 /usr/bin/pip3.9

echo "export LD_LIBRARY_PATH=/usr/local/lib/" > ld_library.sh
mv ld_library.sh /etc/profile.d/ld_library.sh
export set LD_LIBRARY_PATH=/usr/local/lib/

# Install symtem wide python requirements
pip3.9 install -U pip==19.3.1 # As per app servers
pip3.9 install Fabric==1.15.0 # NB: v1.15.0 supports Python 2, & 3.6, 3.7, & 3.8

pip3.9 install mod_wsgi==4.9.4 # As per app servers
ls /usr/local/lib64/python3.12/site-packages/mod_wsgi/server/
pip3.9 install virtualenv==20.24.5 # As per app servers

ln -s /usr/local/bin/virtualenv /usr/bin/virtualenv-3.9

yum -y install python3-pip-wheel-9.0.3-24.el8
yum -y install python3-lxml

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
yum -y update google-chrome
google-chrome --version

# Using system package.  NB: This needs to keep in sync with selenium requirements
yum -y install chromedriver
chromedriver -v

echo "###   Confirm install list"
yum list installed
pip freeze
pip3.9 freeze

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

echo "###   Add new tmp directory location # TODO Add to clamav scan where necessary"
mkdir -p /usr/local/projects/temmpo/var/tmp

touch /usr/local/projects/temmpo/var/log/django.log

chown vagrant:vagrant /usr/local/projects/temmpo/
chown --silent -R vagrant:vagrant /usr/local/projects/temmpo/lib/
chown apache:vagrant /usr/local/projects/temmpo/etc/apache/conf.d
chown -R vagrant:vagrant /usr/local/projects/temmpo/var
chown apache:vagrant /usr/local/projects/temmpo/var/tmp
chown apache:vagrant /usr/local/projects/temmpo/var/abstracts
chown apache:vagrant /usr/local/projects/temmpo/var/data
chown apache:vagrant /usr/local/projects/temmpo/var/results
chown apache:vagrant /usr/local/projects/temmpo/var/email
chown apache:vagrant /usr/local/projects/temmpo/var/www
chown apache:vagrant /usr/local/projects/temmpo/var/log/django.log
chmod -R g+xw /usr/local/projects/temmpo/var/tmp
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

## TODO: Fix path to mod_wsgi module
echo "###   Add basic catch all Apache config normally managed by Puppet"
cat > /etc/httpd/conf.d/temmpo.conf <<APACHE_CONF
LoadModule wsgi_module "/usr/local/lib64/python3.12/site-packages/mod_wsgi/server/mod_wsgi-py312.cpython-36m-x86_64-linux-gnu.so"
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
        'HOST': '10.0.1.20',
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
        'HOST': '10.0.1.20',
        'PORT': '3306',
        'OPTIONS': {
            'sql_mode': 'STRICT_ALL_TABLES'
        }
    },
}

# Prepare for database migration
DATABASES['default'] = DATABASES['mysql']

#DEV ONLY ref https://docs.hcaptcha.com/#integration-testing-test-keys
HCAPTCHA_SITEKEY = '10000000-ffff-ffff-ffff-000000000001'
HCAPTCHA_SECRET = '0x0000000000000000000000000000000000000000'
PRIVATE_SETTINGS
chown -R vagrant:vagrant /usr/local/projects/temmpo/.settings/
chmod -R ug+rwx /usr/local/projects/temmpo/.settings/

# Update locate DB
updatedb
echo "###   See README.md for ways to create virtual environments"
