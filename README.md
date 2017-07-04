# README

## About TeMMPo

*  https://www.temmpo.org.uk/

TeMMPo (Text Mining for Mechanism Prioritisation) is a web-based tool to enable researchers to identify the quantity of published evidence for specific mechanisms between an exposure and outcome. The tool identifies co-occurrence of MeSH headings in scientific publications to indicate papers that link an intermediate mechanism to either an exposure or an outcome.

TeMMPo is particularly useful when a specific lifestyle or dietary exposure is known to associate with a disease outcome, but little is known about the underlying mechanisms. Understanding these mechanisms may help develop interventions, sub-classify disease or establish evidence for causality. TeMMPo quantifies the body of published literature to establish which mechanisms have been researched the most, enabling these mechanisms to be subjected to systematic review.

This development was funded by the World Cancer Research Fund UK, the UK Medical Research Council and the University of Bristol.

## Development

We are using Vagrant for our Centos development environment.  It requires an additional plugin to mount the development source code cloned on your local machine.

### Set up development environment

	vagrant plugin install vagrant-sshfs
	git clone git@bitbucket.org:researchit/temmpo.git

Use one of the techniques below to set up your virtual environment

#### a) Installing a Vagrant development build

	cd deploy
	vagrant up
	vagrant ssh
	fab make_virtualenv:env=dev,configure_apache=False,clone_repo=False,branch=None,migrate_db=True,use_local_mode=True,requirements=base -f /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/fabfile.py

#### b) Installing a Vagrant development build remotely

	cd deploy
	vagrant up
	fab make_virtualenv:env=dev,configure_apache=False,clone_repo=False,branch=None,migrate_db=True,use_local_mode=False,requirements=base  -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200
	vagrant ssh

#### c) Installing a Vagrant Apache build

	cd deploy
	vagrant up db && vagrant up apache
	vagrant ssh apache
	fab make_virtualenv:env=dev,configure_apache=True,clone_repo=True,branch=master,migrate_db=True,use_local_mode=True,requirements=base -f /vagrant/deploy/fabfile.py


#### d) Installing a Vagrant Apache build remotely

	vagrant up db && vagrant up apache
	fab make_virtualenv:env=dev,configure_apache=True,clone_repo=True,branch=master,migrate_db=True,use_local_mode=False,requirements=base -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200
	vagrant ssh apache


### Activate virtualenv

	cd /usr/local/projects/temmpo/lib/dev/bin && source activate


### Move to source directory

	cd /usr/local/projects/temmpo/lib/dev/src/temmpo


### Set up database tables and run any migrations

	python manage.py migrate --database=admin


### Create a super user

	python manage.py createsuperuser --settings=temmpo.settings.dev


### Running tests:

	python manage.py test --settings=temmpo.settings.test

### Run the development server

	python manage.py runserver 0.0.0.0:59099 --settings=temmpo.settings.dev

### View application in your local browser

####  Django server

	http://localhost:59099

####  Apache 

	http://localhost:8800

## Production

### Tag a build
**NB: needs to be run as user with commit rights on the temmpo repo - ie. not the temmpo user**

	git fetch --all
	git checkout master
	git pull
	fab taggit:master,2.4.0,temmpo -f deploy/fabfile.py
	fab taggit:master,prod_stable,temmpo -f deploy/fabfile.py


### Installing a production build remotely, e.g. from the CI server

	ssh ci-p0.rit.bris.ac.uk
	sudo -i -u temmpo

*One off setup*

	mkdir -p /srv/projects/temmpo/lib/git
	cd /srv/projects/temmpo/lib/git
	git clone git@bitbucket.org:researchit/temmpo.git temmpo
	cd /srv/projects/temmpo/lib/git/temmpo
	git fetch --all
	git checkout prod_stable
	git pull
	fab make_virtualenv:env=prod,configure_apache=True,clone_repo=True,branch=prod_stable,migrate_db=True,use_local_mode=False,requirements=base -u temmpo -i /usr/local/projects/temmpo/.ssh/id_rsa.pub -H py-web-p0.epi.bris.ac.uk -f /srv/projects/temmpo/lib/git/temmpo/deploy/fabfile.py

#### Database migration

	cd /srv/projects/temmpo/lib/git/temmpo
	git fetch --all
	git checkout prod_stable
	git pull
	fab sym_link_private_settings:prod,false -u temmpo -i /usr/local/projects/temmpo/.ssh/id_rsa.pub -H py-web-p0.epi.bris.ac.uk -f /srv/projects/temmpo/lib/git/temmpo/deploy/fabfile.py
	fab deploy:env=prod,branch=prod_stable,using_apache=True,migrate_db=True,use_local_mode=False,use_pip_sync=False,requirements=base -u temmpo -i /usr/local/projects/temmpo/.ssh/id_rsa.pub -H py-web-p0.epi.bris.ac.uk -f /srv/projects/temmpo/lib/git/temmpo/deploy/fabfile.py
	fab migrate_sqlite_data_to_mysql:env=prod,use_local_mode=False,using_apache=True,swap_db=True -u temmpo -i /usr/local/projects/temmpo/.ssh/id_rsa.pub -H py-web-p0.epi.bris.ac.uk -f /srv/projects/temmpo/lib/git/temmpo/deploy/fabfile.py

### Each time you want to deploy new code

	cd /srv/projects/temmpo/lib/git/temmpo
	git fetch --all
	git checkout prod_stable
	git pull
	fab deploy:env=prod,branch=prod_stable,using_apache=True,migrate_db=True,use_local_mode=False,use_pip_sync=False,requirements=base -u temmpo -i /usr/local/projects/temmpo/.ssh/id_rsa.pub -H py-web-p0.epi.bris.ac.uk -f /srv/projects/temmpo/lib/git/temmpo/deploy/fabfile.py

## Testing deployment on a development branch on production host, e.g. TMMA-130

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

## Deploy prod_stable branch to Vagrant Apache build

	fab deploy:env=dev,branch=prod_stable,using_apache=True,migrate_db=True,use_local_mode=False,use_pip_sync=False,requirements=base -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200

## Deploy master branch to Vagrant Apache build

	fab deploy:env=dev,branch=master,using_apache=True,migrate_db=True,use_local_mode=False,use_pip_sync=False,requirements=base -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200

## TODO TEST tagging and merging - will need an SSH key with commit rights to the repository:

	fab deploy:env=dev,branch=demo_stable,using_apache=True,tag=2.3,merge_from=master,migrate_db=True,use_local_mode=False,use_pip_sync=False,requirements=base -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200