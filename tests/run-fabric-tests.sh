#!/bin/sh

set -e

cd $GITHUB_WORKSPACE
pip3 install fabric==1.15.0
fab -l -f deploy/fabfile.py