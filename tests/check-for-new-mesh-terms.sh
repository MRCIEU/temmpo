#!/bin/sh

set -e

bash $GITHUB_WORKSPACE/tests/build-test-env.sh

cd $GITHUB_WORKSPACE

# One off previous year - TODO: Remove once this legacy import has been created
fab create_mesh_term_fixtures:env=test,use_local_mode=True,previous_fixture_file=mesh_terms.json,year=2023 -f deploy/fabfile.py
# current year - TODO: Enable once the legacy import has been created
# fab create_mesh_term_fixtures:env=test,use_local_mode=True,previous_fixture_file=mesh_terms.json,year=`date +"%Y"` -f deploy/fabfile.py