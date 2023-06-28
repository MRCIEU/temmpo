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


echo "Check both versions of pip are installed"
pip2 -V
pip3 -V

echo "Install Fabric"
pip2 install -U pip==20.3.4
pip2 install Fabric==1.13.1 # NB: v1.15.0 supports Python 2, & 3.6, 3.7, & 3.8

echo "Install virtualenv"
pip3 install virtualenv==20.13.0

echo "Install wheel"
sudo apt-get install -y python3-wheel-whl

echo "Set up alias for python3.8"
which python3
# which python3.8
# alias python3.8="python3"
which python3.8

cd $GITHUB_WORKSPACE
cd lib/test/src/temmpo

echo "Create virtualenv as per VM based environments"
fab make_virtualenv:env=test,configure_apache=False,clone_repo=False,branch=None,migrate_db=False,use_local_mode=True,requirements=test,restart_rqworker=False,virtualenv=virtualenv,project_dir=$GITHUB_WORKSPACE/ -f deploy/fabfile.py
