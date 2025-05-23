# TeMMPo

[![Run Python/Django test suite](https://github.com/MRCIEU/temmpo/actions/workflows/run-django-test.yml/badge.svg)](https://github.com/MRCIEU/temmpo/actions/workflows/run-django-test.yml)
[![Run Fabric test suite](https://github.com/MRCIEU/temmpo/actions/workflows/run-fabric-test.yml/badge.svg)](https://github.com/MRCIEU/temmpo/actions/workflows/run-fabric-test.yml)

[TeMMPo](https://www.temmpo.org.uk/) (Text Mining for Mechanism Prioritisation) is a web-based tool to enable researchers to identify the quantity of published evidence for specific mechanisms between an exposure and outcome. The tool identifies co-occurrence of MeSH headings in scientific publications to indicate papers that link an intermediate mechanism to either an exposure or an outcome.  TeMMPo is particularly useful when a specific lifestyle or dietary exposure is known to associate with a disease outcome, but little is known about the underlying mechanisms. Understanding these mechanisms may help develop interventions, sub-classify disease or establish evidence for causality. TeMMPo quantifies the body of published literature to establish which mechanisms have been researched the most, enabling these mechanisms to be subjected to systematic review.

## Getting Started

### Prerequisites

* Vagrant [https://www.vagrantup.com/]
* VirtualBox [https://www.virtualbox.org/] or another provider, see [https://www.vagrantup.com/docs/providers/]
NB: The vagrant installation also requires an additional plugin to mount the development source code cloned on your local machine.

Tested with these versions:

* VirtualBox 6.1.32 r149290 (Qt5.6.3)
* Vagrant 2.2.19
* vagrant-sshfs 1.3.6

NB: Additional development IDE support for Visual Code can be added by installing additional packages within your development environment

    cd /usr/local/projects/temmpo/lib/dev/bin
    sudo pip3 install pylint==2.7.4

### Installing

    vagrant plugin install vagrant-sshfs
    git clone git@github.com:MRCIEU/temmpo.git

Use one of the techniques below to set up your virtual environment and create your Django application.
Various options exist.  For example set up with Apache proxying and that by default run database migrations.

#### a. Installing a Vagrant development virtual environment

    cd temmpo/deploy
    vagrant up && vagrant ssh
    fab make_virtualenv:env=dev,configure_apache=False,clone_repo=False,branch=None,migrate_db=True,use_local_mode=True,requirements=dev -f /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/fabfile.py

#### b. Installing a Vagrant development virtual environment using a remotely run Fabric command

    cd temmpo/deploy
    vagrant up && fab make_virtualenv:env=dev,configure_apache=False,clone_repo=False,branch=None,migrate_db=True,use_local_mode=False,requirements=dev  -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200 && vagrant ssh

#### c. Installing a Vagrant Apache fronted virtual environment not mounted to your local development drive

    cd temmpo/deploy
    vagrant up db && vagrant up apache && vagrant ssh apache
    fab make_virtualenv:env=dev,configure_apache=True,clone_repo=True,branch=master,migrate_db=True,use_local_mode=True,requirements=dev -f /vagrant/deploy/fabfile.py

#### d. Installing a Vagrant Apache fronted virtual environment not mounted to your local development drive using a remotely run Fabric command

    cd temmpo/deploy
    vagrant up db && vagrant up apache && fab make_virtualenv:env=dev,configure_apache=True,clone_repo=True,branch=master,migrate_db=True,use_local_mode=False,requirements=dev -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200 && vagrant ssh apache

### Other useful commands

#### Activate virtualenv and move to source directory

    cd /usr/local/projects/temmpo/lib/dev/bin && source activate && cd /usr/local/projects/temmpo/lib/dev/src/temmpo

#### Create a super user

    python manage.py createsuperuser --settings=temmpo.settings.dev

#### Importing MeSH Terms

To be able to run the applications browsing and searching functionality Mesh Terms will need to be imported, either by using fixtures or the custom management command.

1. Load fixture data

NB: this can take a few minutes.

    python manage.py loaddata browser/fixtures/mesh_terms_2015_2018_2019_2020.json  --settings=temmpo.settings.dev

1. Management command

    Annually MeSH terms are released.  This can be as early as November for the following year.  There is a management command that can be run annually once the new terms have been sourced.  Reference: ftp://nlmpubs.nlm.nih.gov/online/mesh/MESH_FILES/meshtrees/ or see newer location: ftp://nlmpubs.nlm.nih.gov/online/mesh/MESH_FILES/meshtrees/mtrees2021.bin

    NB: This command each take over 50 minutes to run depending on your environment.

        python manage.py import_mesh_terms ./temmpo/prepopulate/mtrees2021.bin 2021

##### Dumping MeSH terms to a fixture file

After importing a new year of mesh terms, create a fixture file for testing and development purposes.  For example:

    python manage.py dumpdata browser.MeshTerm --indent 4 --output browser/fixtures/mesh_terms_2015_2018_2019_2020_2021.json

#### Importing Genes - optional

A database of existing gene terms can be imported into the Django application database, either by using fixtures or the slower custom management command.

1. Load fixture data

    NB: This can take a few minutes.

        python manage.py loaddata browser/fixtures/genes_snap_shot_2020_06_29.json --settings=temmpo.settings.dev

2. Management command

    A sample set is stored and loaded from this GENE_FILE_LOCATION setting location.

        python manage.py import_genes --settings=temmpo.settings.dev

#### Run the development server and workers

In development you will need to restart the worker whenever any changes to the matching code are made.  Run the following in a separate window and restart to see changes to the mathcing code.

    fab restart_rqworker_service:use_local_mode=True -f /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/fabfile.py

In a separate terminal window run the development server

    python manage.py runserver 0.0.0.0:59099 --settings=temmpo.settings.dev

#### View application in your local browser

##### Using Django development server

    http://localhost:59099

##### Using Apache as a proxy server

    http://localhost:8800

#### Database migrations

NB: If you want to manually run migrations you need to use the --database flag

    python manage.py migrate --database=admin --settings=temmpo.settings.dev

#### Updating the requirements file using pip-tools (via Vagrant VM)

NB: This can take a while as we also generate hashes for additional security.

    fab pip_sync_requirements_file:env=dev,use_local_mode=True -f /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/fabfile.py

Optionally pass in a package or update them all within any requirements.in file constraints

    fab pip_tools_update_requirements:env=dev,use_local_mode=True,package="" -f /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/fabfile.py

Alternatively a Python (Debian) base docker image to update requirements

    docker build -f deploy/Dockerfile -t temmpo-web .
    docker run --rm -it -v $PWD:/srv -w /srv temmpo-web bash /srv/entrypoints/update-requirements.sh

Alternatively build a RHEL base docker image to update requirements

    docker compose build web
    docker compose run --rm --no-deps web bash ./entrypoints/update-requirements.sh

#### Create Docker images for different environments

    docker build -f deploy/Dockerfile -t temmpo-web-dev . --build-arg REQUIREMENTS_FILE=dev.txt

    docker build -f deploy/Dockerfile -t temmpo-web-test . --build-arg REQUIREMENTS_FILE=test.txt

example dev command

    docker run --rm -it -v $PWD:/srv -w /srv temmpo-web-dev bash /srv/entrypoints/django-upgrade.sh

#### Development deployment commands when working with the apache Vagrant VM

##### a. Deploy master branch to Vagrant Apache VM

    fab deploy:env=dev,branch=master,using_apache=True,migrate_db=True,use_local_mode=False,use_pip_sync=True,requirements=base -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200

##### b. Deploy demo_stable branch on Vagrant Apache VM

    fab deploy:env=dev,branch=demo_stable,using_apache=True,migrate_db=True,use_local_mode=False,use_pip_sync=True,requirements=base -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200

##### c. Deploy prod_stable branch to Vagrant Apache VM

    fab deploy:env=dev,branch=prod_stable,using_apache=True,migrate_db=True,use_local_mode=False,use_pip_sync=True,requirements=base -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200

## Running the tests

Entire test suite

    cd /usr/local/projects/temmpo/lib/dev/bin && source activate && cd /usr/local/projects/temmpo/lib/dev/src/temmpo

    python manage.py test --settings=temmpo.settings.test_mysql

Run the entire test suite using MySQL and generate a coverage report.

    coverage run --source='.' manage.py test --settings=temmpo.settings.test_mysql && coverage report --skip-empty --skip-covered -m

### Running specific tests

e.g. Just the searching related tests and fail at the first error

    python manage.py test tests.test_searching --settings=temmpo.settings.test_mysql --failfast

e.g. Skipping slow tests

    python manage.py test --settings=temmpo.settings.test_mysql --exclude-tag=slow

e.g. Skipping selenium and clamav tests

    python manage.py test --settings=temmpo.settings.test_mysql --exclude-tag=selenium-test --exclude-tag=clamav

e.g. Run selenium tests only

    python manage.py test --settings=temmpo.settings.test_mysql --tag=selenium-test

### Running Cypress Tests locally

Using a locally instally node environment

NB: Some tests require these environment variables `CREDENTIALS_USR` and `CREDENTIALS_PSW` to be defined, to be able log into the site being tested.  These details can be found in Research IT's LastPass account.  Based on the `cypress.example.env.json` create a `cypress.env.json` file and fill in the details required from LastPass.

    npx cypress open

Using docker and electron browser

    docker run --rm -it -v $PWD:/e2e -w /e2e cypress/included:14.3.3

## Warnings

    IntegrityError at /search/ovidmedline/
    (1048, "Column 'mesh_terms_year_of_release' cannot be null")

This suggests attempting to create a search when no mesh terms have been imported into the database as yet.

## Debugging issues

The project needs the following additional services to be running:

    sudo systemctl status redis
    sudo systemctl status rqworker1
    sudo systemctl status rqworker2
    sudo systemctl status rqworker3
    sudo systemctl status rqworker4
    sudo systemctl status httpd      # Not relevant for the django Vagrant VM

### Check all services

    sudo systemctl status

## Built with

* [2015, 2018, & 2019 MeSH®](https://www.nlm.nih.gov/mesh/meshhome.html) - Medical Subject Headings terms provided by U.S. National Library of Medicine
* [Apache](https://www.apache.org/) - Web server/proxy
* [Centos](https://centos.org/) - Operating System
* [D3 Data-Driven Documents](https://d3js.org/) - Visualization tools
* [DataTables](https://datatables.net/license/mit) - Dynamic UI
* [Django](https://www.djangoproject.com/) - Web framework
* [Google Charts](https://developers.google.com/chart/) - Visualization tools
* [Jenkins](https://jenkins.io) - Continuous Integration/Deployment
* [jsTree](https://github.com/vakata/jstree) - Dynamic UI
* [MEDLINE®](https://www.nlm.nih.gov/bsd/medline.html) - Export format of the National Library of Medicine® (NLM®) journal citation database
* [MySQL](https://www.mysql.com) - Database server
* [Puppet](https://puppet.com/) - Configuration management
* [Python](https://www.python.org/) - Programming language
* [Redis](https://redis.io/) - Message queue
* [SB Admin 2](https://startbootstrap.com/template-overviews/sb-admin-2/) - Web design

## Versioning

For the versions available, see the [CHANGELOG](CHANGELOG) and the tags on this repository.

## Authors

* Tom Gaunt - Initial code - MRC Integrative Epidemiology Unit
* Ben Elsworth - Code contributions - MRC Integrative Epidemiology Unit
* Tessa Alexander - Developer - Research IT, University of Bristol
* Kieren Pitts - Developer cover - Research IT, University of Bristol
* Jon Hallett - Systems Administrator - Research IT, University of Bristol
* Mike Rodwell - Acceptance testing - Research IT, University of Bristol
* Rick Henry - Systems Administrator - Research IT, University of Bristol

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details

## Acknowledgements

* Funded by World Cancer Research Fund UK
* Funded by UK Medical Research Council (MRC)
* Conceived by the MRC Integrative Epidemiology Unit, University of Bristol
* Packaged and developed by Research IT, University of Bristol
* Hosting infrastructure provided by IT Services, University of Bristol
