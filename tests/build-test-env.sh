#!/bin/sh

set -e

cd $GITHUB_WORKSPACE
echo "Move source code to a directory structure the application expects"
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


echo "Check the version of pip that is installed"
pip3 -V
echo "Ensure using a consistent version of pip as per on premises CI server"
pip3 install -U pip==22.0.2
pip3 -V

echo "Install Fabric"
pip3 install fabric==1.15.0 # NB: v1.15.0 supports Python 2, & 3.6, 3.7, & 3.8

echo "Install virtualenv"
pip3 install virtualenv==15.1.0

echo "Install wheel"
sudo apt-get install -y python3-wheel-whl

echo "Check aliases for python3.8"
which python3
which python3.8

echo "Install Chrome"
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt-get install -y ./google-chrome-stable_current_amd64.deb
rm -f google-chrome-stable_current_amd64.deb
which google-chrome
google-chrome --version

cd $GITHUB_WORKSPACE
cd lib/test/src/temmpo

echo "Create virtualenv as per VM based environments"
fab make_virtualenv:env=test,configure_apache=False,clone_repo=False,branch=None,migrate_db=False,use_local_mode=True,requirements=test,restart_rqworker=False,virtualenv=virtualenv,project_dir=$GITHUB_WORKSPACE/ -f deploy/fabfile.py

cd $GITHUB_WORKSPACE