echo "###   Create directories normally managed by Puppet"
mkdir -p /usr/local/projects/temmpo/etc/apache/conf.d
mkdir -p /usr/local/projects/temmpo/etc/ssl
mkdir -p /usr/local/projects/temmpo/lib/${ENVIRON}/lib
mkdir -p /usr/local/projects/temmpo/.settings
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