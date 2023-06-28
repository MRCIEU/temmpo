#!/bin/sh

set -e

bash $GITHUB_WORKSPACE/tests/build-test-env.sh

echo "Run coverage tests"
cd $GITHUB_WORKSPACE
cd lib/test/src/temmpo
../../bin/coverage
../../bin/coverage run --source='.' manage.py test --settings=temmpo.settings.test_mysql --exclude-tag=selenium-test --exclude-tag=skip-on-ubuntu
../../bin/coverage report --skip-empty --skip-covered -m
