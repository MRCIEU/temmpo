#!/bin/bash
set -e

echo "Run Django checks"
python3 manage.py check

echo "Collect static"
python3 manage.py collectstatic --no-input

echo "Run Django tests"
python3 manage.py test --noinput --parallel

# --parallel 
# --failfast
# --tag TMMA-???
# --keepdb
