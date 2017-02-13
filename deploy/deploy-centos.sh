echo "Build script for TeMMPo"

sudo yum -y install epel-release
sudo yum -y update

sudo yum -y install python-devel
sudo yum -y install python-wheel
sudo yum -y install python-magic
sudo yum -y install libxml2-python
sudo yum -y install libxml2-devel
sudo yum -y install libxslt-python
sudo yum -y install libxslt-devel
sudo yum -y install python-lxml

# install gcc
sudo yum -y install gcc gcc-c++

# mariadb dev stuff
sudo yum -y install mariadb-devel

# dev tools
sudo yum -y install git
sudo yum -y install nano

# Web server setup
# httpd mod_wsgi cronolog

# Python application dependencies

echo "Install virtual env with pip"
sudo pip install virtualenv

echo "Create virtual environment in this location:"
cd /var/local/
virtualenv --system-site-packages -p /usr/bin/python2 temmpo
cd temmpo
ls -l
echo "Create required sub directories"
mkdir -p etc
mkdir -p src
mkdir -p var/results
mkdir -p logs

echo "Load base application requirements"
cd src/temmpo
../../bin/pip install -r requirements/base.txt

# # contexts that are required for application to run behind Apache
# # TODO: review if semanage should be used instead
# # https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Security-Enhanced_Linux/sect-Security-Enhanced_Linux-SELinux_Contexts_Labeling_Files-Persistent_Changes_semanage_fcontext.html#sect-Security-Enhanced_Linux-SELinux_Contexts_Labeling_Files-Persistent_Changes_semanage_fcontext
# sudo chcon -R -t httpd_sys_rw_content_t /var/local/temmpo/logs
# sudo chcon -R -t httpd_sys_rw_content_t /var/local/temmpo/var
# sudo chcon -R -t httpd_sys_script_exec_t /var/local/temmpo/lib/python2.7/site-packages/

# # Production excptions - clone prod stable
# # NB: Would require requirements/prod.txt