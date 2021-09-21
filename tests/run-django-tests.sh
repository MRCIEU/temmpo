#!/bin/sh

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
cd $GITHUB_WORKSPACE
cd lib/test/src/temmpo
pip3 install -U pip==20.3.3
pip3 install setuptools==50.3.2
pip3 install pip-tools==5.4.0
pip3 freeze
pip3 install -r requirements/requirements.txt
pip-sync requirements/test.txt
cd $GITHUB_WORKSPACE
cd lib/test/src/temmpo
coverage
coverage run --source='.' manage.py test --settings=temmpo.settings.test_mysql --exclude-tag=selenium-test --exclude-tag=slow
coverage report --skip-empty --skip-covered -m
coverage run --source='.' manage.py test --settings=temmpo.settings.test_mysql --exclude-tag=selenium-test --tag=slow
coverage report --skip-empty --skip-covered -m