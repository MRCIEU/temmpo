#!/bin/sh

cd /srv
find /srv -name "*.py" | xargs django-upgrade --target-version 4.2
