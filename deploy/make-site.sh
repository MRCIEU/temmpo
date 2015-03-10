# DEV site

mkdir var # Ensure writeable by webserver 

virtualenv --no-site-packages beta
cd beta
bin/pip install django # Tested with 1.7.4
bin/pip install django-chunked-upload # Trailing
bin/pip install django-bft # Trailing
bin/pip install recaptcha-client
# bin/pip install Flask
# Look at https://pypi.python.org/pypi/django-bft

# TODO: Add deploy to Apache Fabric or shell based script 



# MEDIA_ROOT = set 