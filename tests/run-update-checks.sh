#!/bin/sh

set -e

cd $GITHUB_WORKSPACE
cd lib/test/src/temmpo

echo "Generate updates"
fab pip_sync_requirements_file:env=test,use_local_mode=True -f /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/fabfile.py