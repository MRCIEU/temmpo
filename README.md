# README #

## About TeMMPo ##

*  https://www.temmpo.org.uk/

TeMMPo (Text Mining for Mechanism Prioritisation) is a web-based tool to enable researchers to identify the quantity of published evidence for specific mechanisms between an exposure and outcome. The tool identifies co-occurrence of MeSH headings in scientific publications to indicate papers that link an intermediate mechanism to either an exposure or an outcome.

TeMMPo is particularly useful when a specific lifestyle or dietary exposure is known to associate with a disease outcome, but little is known about the underlying mechanisms. Understanding these mechanisms may help develop interventions, sub-classify disease or establish evidence for causality. TeMMPo quantifies the body of published literature to establish which mechanisms have been researched the most, enabling these mechanisms to be subjected to systematic review.

This development was funded by the World Cancer Research Fund UK, the UK Medical Research Council and the University of Bristol.

## Development ##

We are using Vagrant for our Centos development environment.  It requires an additional plugin to mount the development source code cloned on your local machine.

# Set up development environment

vagrant plugin install vagrant-sshfs
git clone git@bitbucket.org:researchit/temmpo.git

cd temmpo/deploy
vagrant up
vagrant ssh

# Activate virtualenv
cd /srv/projects/temmpo/lib/dev/bin && source activate

# Move to source directory
cd /srv/projects/temmpo/lib/dev/src/temmpo

# Set up database tables and run any migrations
python manage.py migrate

# Create a super user
python manage.py createsuperuser --settings=temmpo.settings.dev

# Running tests:
python manage.py test --settings=temmpo.settings.dev

# Run the development server
python manage.py runserver 0.0.0.0:59099 --settings=temmpo.settings.dev

## Deployment ##

# Tag in git using fabric utility function

# Tag release, e.g. version 1.2
fab taggit:master,1.3,temmpo

# Move/update prod_stable branch 
fab taggit:master,prod_stable,temmpo

## Deployment helper functions

# Example deploy feature branch to development server
fab deploy:host="tmma-dev.ilrt.bris.ac.uk",env="dev",branch="demo_stable",merge_from="TMMA-155"
fab deploy:host="tmma-dev.ilrt.bris.ac.uk",env="dev",branch="demo_stable",merge_from="TMMA-155" -i /srv/projects/tmma/.ssh/id_rsa.pub -u tmma

# Example deploy to production and tag master with a numeric version number
fab deploy:host="tmma.ilrt.bris.ac.uk",env="prod",branch="prod_stable",tag=1.4,merge_from="master" -i /srv/projects/tmma/.ssh/id_rsa.pub -u tmma


# On production environment, e.g.
cd /usr/local/projects/tmma/lib/prod/src/temmpo

# One off
git branch --set-upstream prod_stable origin/prod_stable

git pull

../../bin/python manage.py collectstatic --dry-run
../../bin/python manage.py collectstatic

../../bin/python manage.py migrate browser

## Installation ##

# Installing a Vagrant development build

cd deploy
vagrant up
vagrant ssh
fab make_virtualenv:env=dev,configure_apache=False,clone_repo=False,branch=None,migrate_db=True,use_local_mode=True,requirements=base -f /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/fabfile.py

# Installing a Vagrant Apache build

cd deploy
vagrant up apache
vagrant ssh apache
fab make_virtualenv:env=dev,configure_apache=True,clone_repo=True,branch=master,migrate_db=True,use_local_mode=True,requirements=base -f /vagrant/deploy/fabfile.py

## Installing a Vagrant Apache build remotely

vagrant up apache
fab make_virtualenv:env=dev,configure_apache=True,clone_repo=True,branch=master,migrate_db=True,use_local_mode=False,requirements=base -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2222


## Installing a production build remotely, e.g. from the CI server

ssh ci-p0.rit.bris.ac.uk
sudo -i -u temmpo

# ONE OFF
mkdir -p /srv/projects/temmpo/lib/git
cd /srv/projects/temmpo/lib/git
git clone git@bitbucket.org:researchit/temmpo.git temmpo

# TAG BUILD (needs to be run as user with commit rights on the temmpo repo - ie. not temmpo)
git fetch --all
git checkout master
git pull
fab taggit:master,2.3,temmpo -f deploy/fabfile.py
fab taggit:master,prod_stable,temmpo -f deploy/fabfile.py

# EACH TIME
cd /srv/projects/temmpo/lib/git/temmpo
git fetch --all
git checkout prod_stable
git pull

fab make_virtualenv:env=prod,configure_apache=True,clone_repo=True,branch=prod_stable,migrate_db=True,use_local_mode=False,requirements=base -u temmpo -i /usr/local/projects/temmpo/.ssh/id_rsa.pub -H py-web-p0.epi.bris.ac.uk -f /srv/projects/temmpo/lib/git/temmpo/deploy/fabfile.py


## Testing deployment on a development, e.g. TMMA-130, branch on production host
ssh ci-p0.rit.bris.ac.uk
sudo -i -u temmpo
mkdir -p /srv/projects/temmpo/lib/git
cd /srv/projects/temmpo/lib/git
git clone git@bitbucket.org:researchit/temmpo.git temmpo
cd /srv/projects/temmpo/lib/git/temmpo
git fetch --all
git checkout TMMA-130
git pull
fab make_virtualenv:env=prod,configure_apache=True,clone_repo=True,branch=TMMA-130,migrate_db=True,use_local_mode=False,requirements=base -u temmpo -i /usr/local/projects/temmpo/.ssh/id_rsa.pub -H py-web-p0.epi.bris.ac.uk -f /srv/projects/temmpo/lib/git/temmpo/deploy/fabfile.py