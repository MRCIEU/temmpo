#!/bin/sh

set -e

bash $GITHUB_WORKSPACE/tests/build-test-env.sh

echo "Run coverage tests"
cd $GITHUB_WORKSPACE
cd lib/test/src/temmpo
../../bin/coverage
# TODO revert to runnign all tests
../../bin/coverage run --source='.' manage.py test --settings=temmpo.settings.test_mysql --tag mimetype --exclude-tag=selenium-test
../../bin/coverage report --skip-empty --skip-covered -m
