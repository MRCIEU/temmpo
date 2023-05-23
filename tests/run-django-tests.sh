#!/bin/sh

set -e

cd $GITHUB_WORKSPACE
# Move source code to a directory structure the application expects.
mkdir -p lib/test/src/temmpo
shopt -s extglob
mv !(lib) lib/test/src/temmpo/
cd lib/test/src/temmpo/temmpo/settings/
ln -s github_actions_ci_private_settings.py private_settings.py
pwd
ls
cd $GITHUB_WORKSPACE
mkdir -p var/abstracts
mkdir -p var/data
mkdir -p var/log
mkdir -p var/results/testing/v1
mkdir -p var/results/testing/v3
mkdir -p var/results/testing/v4
mkdir -p var/tmp


# Check both versions of pip are installed
pip2 -V
pip3 -V

# Install Fabric
pip2 install -U pip==19.3.1
pip2 install Fabric==1.13.1 # NB: v1.15.0 supports Python 2, & 3.6, 3.7, & 3.8

# Install virtualenv
pip3.8 install virtualenv==20.13.0

cd $GITHUB_WORKSPACE
cd lib/test/src/temmpo

# Create virtualenv as per VM based environments
fab make_virtualenv:env=test,configure_apache=False,clone_repo=False,branch=None,migrate_db=True,use_local_mode=True,requirements=test,restart_rqworker=False -f deploy/fabfile.py

# pip3 install -U pip==23.1.2
# pip3 install setuptools==67.8.0
# pip3 install pip-tools==6.13.0
# pip3 freeze
# pip3 install -r requirements/requirements.txt
# pip-sync requirements/test.txt
# cd $GITHUB_WORKSPACE
# cd lib/test/src/temmpo
coverage
coverage run --source='.' manage.py test --settings=temmpo.settings.test_mysql --exclude-tag=selenium-test --exclude-tag=skip-on-ubuntu
coverage report --skip-empty --skip-covered -m
