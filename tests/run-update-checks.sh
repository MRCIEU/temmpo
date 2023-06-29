#!/bin/sh

set -e

bash $GITHUB_WORKSPACE/tests/build-test-env.sh

cd $GITHUB_WORKSPACE
cd lib/test/src/temmpo

echo "Generate any updates to requirements files"
fab pip_sync_requirements_file:env=test,use_local_mode=True,project_dir=$GITHUB_WORKSPACE/ -f deploy/fabfile.py

# Move code back to expected location for pull request
cd $GITHUB_WORKSPACE

ls lib/test/src/temmpo
mv lib/test/src/temmpo/* $GITHUB_WORKSPACE
ls
ls -l requirements