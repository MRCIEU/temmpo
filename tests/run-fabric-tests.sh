#!/bin/sh

set -e

cd $GITHUB_WORKSPACE
pip install fabric==1.13.1
fab -l -f deploy/fabfile.py