echo "Build script for TeMMPo"

sudo yum -y install epel-release
sudo yum -y update
sudo yum -y install python-devel
sudo yum -y install python-wheel
sudo yum -y install python-magic

sudo yum -y install python-virtualenv
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
sudo yum -y install httpd 
sudo yum -y install mod_wsgi 
# sudo yum -y install cronolog  # TODO: Add to production Centos puppet config

# Python application dependencies

echo "Create virtual environment in this location:"
mkdir -p /srv/projects/temmpo/lib/
cd /srv/projects/temmpo/lib/
# Ensure use Python 2.7 is used
virtualenv --system-site-packages -p /usr/bin/python2 dev
cd dev
ls -l
echo "Create required sub directories"
mkdir -p /srv/projects/temmpo/etc
# TODO: Non vagrant build need to create and clone the repo in the src directory
# mkdir -p src
# cd src 
# git clone git@bitbucket.org:researchit/temmpo.git
mkdir -p /srv/projects/temmpo/lib/dev/var/results
mkdir -p /srv/projects/temmpo/lib/dev/var/abstracts

echo "Load base application requirements"
cd /srv/projects/temmpo/lib/dev/
./bin/pip install -r src/temmpo/requirements/dev.txt

# # contexts that are required for application to run behind Apache
# # TODO: review if semanage should be used instead
# # https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/6/html/Security-Enhanced_Linux/sect-Security-Enhanced_Linux-SELinux_Contexts_Labeling_Files-Persistent_Changes_semanage_fcontext.html#sect-Security-Enhanced_Linux-SELinux_Contexts_Labeling_Files-Persistent_Changes_semanage_fcontext
# sudo chcon -R -t httpd_sys_rw_content_t /var/local/temmpo/logs
# sudo chcon -R -t httpd_sys_rw_content_t /var/local/temmpo/var
# sudo chcon -R -t httpd_sys_script_exec_t /var/local/temmpo/lib/python2.7/site-packages/

# # Production exceptions - clone prod stable
# # NB: Would require requirements/prod.txt

cd /srv/projects/temmpo/lib/
chown --silent -R vagrant:vagrant dev

echo "Creating SQLite database"
cd /srv/projects/temmpo/lib/dev/src/temmpo
sudo -u vagrant ../../bin/python manage.py migrate --settings=temmpo.settings.dev

echo "Run tests"
sudo -u vagrant ../../bin/python manage.py test --settings=temmpo.settings.dev

echo "TODO: populate the mesh terms - import_mesh_terms import_genes"

echo "## MANUAL STEP 1 Create superuser ##"
echo "cd /srv/projects/temmpo/lib/dev/src/temmpo && ../../bin/python manage.py createsuperuser --settings=temmpo.settings.dev"

echo "## MANUAL STEP 2 ## Run the dev server ##"
echo "cd /srv/projects/temmpo/lib/dev/src/temmpo && ../../bin/python manage.py runserver 0.0.0.0:59099 --settings=temmpo.settings.dev"
echo "Open http://127.0.0.1:59099 in your local web browser"
