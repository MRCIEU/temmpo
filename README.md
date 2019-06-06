# README

## About TeMMPo

* URL: https://www.temmpo.org.uk/
* Wiki: https://wikis.bris.ac.uk/display/rit/TeMMPo:+Text+Mining+for+Mechanism+Prioritisation

TeMMPo (Text Mining for Mechanism Prioritisation) is a web-based tool to enable researchers to identify the quantity of published evidence for specific mechanisms between an exposure and outcome. The tool identifies co-occurrence of MeSH headings in scientific publications to indicate papers that link an intermediate mechanism to either an exposure or an outcome.

TeMMPo is particularly useful when a specific lifestyle or dietary exposure is known to associate with a disease outcome, but little is known about the underlying mechanisms. Understanding these mechanisms may help develop interventions, sub-classify disease or establish evidence for causality. TeMMPo quantifies the body of published literature to establish which mechanisms have been researched the most, enabling these mechanisms to be subjected to systematic review.

This development was funded by the World Cancer Research Fund UK, the UK Medical Research Council and the University of Bristol.

## Development

We are using Vagrant for our Centos development environment.  It requires an additional plugin to mount the development source code cloned on your local machine.

### Set up development environment

    vagrant plugin install vagrant-sshfs
    git clone git@bitbucket.org:researchit/temmpo.git

Use one of the techniques below to set up your virtual environment and create your Django application.
Various options exist.  Optionally front with Apache, by default run database migrations.

#### a. Installing a Vagrant development virtual environment.

    cd temmpo/deploy
    vagrant up && vagrant ssh
    fab make_virtualenv:env=dev,configure_apache=False,clone_repo=False,branch=None,migrate_db=True,use_local_mode=True,requirements=dev -f /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/fabfile.py

#### b. Installing a Vagrant development virtual environment using remotely run Fabric command.

    cd temmpo/deploy
    vagrant up && fab make_virtualenv:env=dev,configure_apache=False,clone_repo=False,branch=None,migrate_db=True,use_local_mode=False,requirements=dev  -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200 && vagrant ssh

#### c. Installing a Vagrant Apache fronted virtual environment not mounted to your local development drive.

    cd temmpo/deploy
    vagrant up db && vagrant up apache && vagrant ssh apache
    fab make_virtualenv:env=dev,configure_apache=True,clone_repo=True,branch=master,migrate_db=True,use_local_mode=True,requirements=base -f /vagrant/fabfile.py


#### d. Installing a Vagrant Apache fronted virtual environment not mounted to your local development drive using remotely run Fabric command,

    cd temmpo/deploy
    vagrant up db && vagrant up apache && fab make_virtualenv:env=dev,configure_apache=True,clone_repo=True,branch=master,migrate_db=True,use_local_mode=False,requirements=base -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200 && vagrant ssh apache


### Activate virtualenv and move to source directory

    cd /usr/local/projects/temmpo/lib/dev/bin && source activate && cd /usr/local/projects/temmpo/lib/dev/src/temmpo


### Create a super user

    python manage.py createsuperuser --settings=temmpo.settings.dev

### Importing MeSH Terms

To be able to run the applications browsing and searching functionality Mesh Terms will need to be imported, either by using fixtures or the custom management command.

1. Load fixture data

    NB: this can take a few minutes.

        python manage.py loaddata browser/fixtures/mesh_terms_2015_2018.json  --settings=temmpo.settings.dev

2. Management command

    Annually MeSH terms are released.  This can be as early as November for the following year.  There is a management command that can be run annually once the new terms have been sourced.  Reference: ftp://nlmpubs.nlm.nih.gov/online/mesh/MESH_FILES/meshtrees/

    NB: This command each take over 20 minutes to run.

        python manage.py import_mesh_terms ./temmpo/prepopulate/mtrees2019.bin 2019

### Importing Genes - optional

A database of existing gene terms can be imported into the Django application database.  A sample set is stored and loaded from this GENE_FILE_LOCATION setting location.

    python manage.py import_genes --settings=temmpo.settings.dev

### Run the development server and workers

    # Ensure matching code is reloaded

    sudo systemctl stop rqworker
    python manage.py rqworker default --settings=temmpo.settings.dev

    # In a separate terminal window run the development server
    
    python manage.py runserver 0.0.0.0:59099 --settings=temmpo.settings.dev

### View application in your local browser

####  Using Django development server

    http://localhost:59099

####  Using Apache as a proxy server

    http://localhost:8800

### Running tests:

    python manage.py test --settings=temmpo.settings.test_mysql

    or

    python manage.py test --settings=temmpo.settings.test_sqlite

#### Running specific tests

e.g. Just the searching related tests and fail at the first error

    python manage.py test tests.test_searching --settings=temmpo.settings.test_mysql --failfast

### Database migrations

NB: If you want to manually run migrations you need to use the --database flag

    python manage.py migrate --database=admin --settings=temmpo.settings.dev

### Updating the requirements file using pip-sync (via Vagrant VM)

    fab pip_sync_requirements_file:env=dev,use_local_mode=True -f /usr/local/projects/temmpo/lib/dev/src/temmpo/deploy/fabfile.py

### Development deployment commands when working with the apache Vagrant VM.

#### a. Deploy master branch to Vagrant Apache VM

    fab deploy:env=dev,branch=master,using_apache=True,migrate_db=True,use_local_mode=False,use_pip_sync=True,requirements=base -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200

#### b. Deploy demo_stable branch on Vagrant Apache VM:

    fab deploy:env=dev,branch=demo_stable,using_apache=True,migrate_db=True,use_local_mode=False,use_pip_sync=True,requirements=base -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200

#### c. Deploy prod_stable branch to Vagrant Apache VM

    fab deploy:env=dev,branch=prod_stable,using_apache=True,migrate_db=True,use_local_mode=False,use_pip_sync=True,requirements=base -u vagrant -i ~/.vagrant.d/insecure_private_key -H 127.0.0.1:2200

## Production

### Deploying changes to the production site, https://www.temmpo.org.uk/

The Research IT Jenkins continuous integration server is used to deploy code to the production website.  This job is manually triggered simply by building this job:

https://ci-p0.rit.bris.ac.uk/job/TeMMPo/job/Production/job/1-merge-prod-stable-branch/

Below are the shell commands that each part of the CI pipeline runs from the CI server ci-p0.rit.bris.ac.uk:

1. Project 1-merge-prod-stable-branch

        if [ ! -d temmpo ] ; then git clone git@bitbucket.org:researchit/temmpo.git; fi
        cd temmpo
        git fetch origin
        git checkout demo_stable
        git pull
        git checkout prod_stable
        git pull origin prod_stable
        git merge -m "RIT Jenkins CI merged demo_stable into prod_stable branch before deployment" demo_stable
        git push origin prod_stable

    Upon success the following job is triggered.

2. Project 2-deploy-production

        fab deploy:env=prod,branch=prod_stable,using_apache=True,migrate_db=True,use_local_mode=False,use_pip_sync=True,requirements=base -u temmpo -H py-web-p0.epi.bris.ac.uk -f deploy/fabfile.py  --forward-agent

3. Project 3-tag-prod-stable

        git tag -a deployed_on_prod_${BUILD_TIMESTAMP} -m "RIT Jenkins CI deployed the production site on ${BUILD_TIMESTAMP}"
        git push origin deployed_on_prod_${BUILD_TIMESTAMP}

NB: The Jenkins jobs are configured to use the CI server's temmpo user account's SSH keys /usr/local/projects/temmpo/.ssh/id_rsa.pub and the rit-temmpo-ci Bitbucket user's SSH key.

### To build a production Python virtual environment from the CI server

*One off setup*

    ssh ci-p0.rit.bris.ac.uk
    sudo -i -u temmpo
    cd /srv/projects/temmpo/lib/git/temmpo/
    git fetch origin
    git checkout master
    git pull
    fab make_virtualenv:env=prod,configure_apache=True,clone_repo=True,branch=prod_stable,migrate_db=True,use_local_mode=False,requirements=base -u temmpo -i /usr/local/projects/temmpo/.ssh/id_rsa.pub -H py-web-p0.epi.bris.ac.uk -f /srv/projects/temmpo/lib/git/temmpo/deploy/fabfile.py

### Database transfer from SQLlite to MySQL - *Legacy*

How data was migrated from SQLite to MySQL

    cd /srv/projects/temmpo/lib/git/temmpo
    git fetch --all
    git checkout prod_stable
    git pull
    fab sym_link_private_settings:prod,false -u temmpo -i /usr/local/projects/temmpo/.ssh/id_rsa.pub -H py-web-p0.epi.bris.ac.uk -f /srv/projects/temmpo/lib/git/temmpo/deploy/fabfile.py
    fab deploy:env=prod,branch=prod_stable,using_apache=True,migrate_db=True,use_local_mode=False,use_pip_sync=False,requirements=base -u temmpo -i /usr/local/projects/temmpo/.ssh/id_rsa.pub -H py-web-p0.epi.bris.ac.uk -f /srv/projects/temmpo/lib/git/temmpo/deploy/fabfile.py
    fab migrate_sqlite_data_to_mysql:env=prod,use_local_mode=False,using_apache=True,swap_db=True -u temmpo -i /usr/local/projects/temmpo/.ssh/id_rsa.pub -H py-web-p0.epi.bris.ac.uk -f /srv/projects/temmpo/lib/git/temmpo/deploy/fabfile.py

## Demo

### Deploying changes to the demo site, https://py-web-d0.epi.bris.ac.uk/

The Research IT Jenkins continuous integration server is used to deploy code to the demo website.  Periodically changes that have been moved onto the last_known_good will be deployed onto the demo server.  See: https://ci-p0.rit.bris.ac.uk/job/TeMMPo/job/Demo%20jobs/job/1-merge-demo-branch-project/

Below are the shell commands that each part of the CI pipeline runs from the CI server ci-p0.rit.bris.ac.uk:

1. Project 1-merge-demo-branch-project

        if [ ! -d temmpo ] ; then git clone git@bitbucket.org:researchit/temmpo.git; fi
        cd temmpo
        git fetch origin
        git checkout last_known_good
        git pull
        git checkout demo_stable
        git pull origin demo_stable
        git merge -m "RIT Jenkins CI merged last_known_good into demo_stable branch before deployment" last_known_good
        git push origin demo_stable

2. Project 2-deploy-demo-project

        fab deploy:env=demo,branch=demo_stable,using_apache=True,migrate_db=True,use_local_mode=False,use_pip_sync=True,requirements=base -u temmpo -H py-web-d0.epi.bris.ac.uk -f deploy/fabfile.py  --forward-agent

3. Project 3-tag-demo-stable-project

        git tag -a deployed_on_demo_${BUILD_TIMESTAMP} -m "RIT Jenkins CI deployed demo site on ${BUILD_TIMESTAMP}"
        git push origin deployed_on_demo_${BUILD_TIMESTAMP}

NB: The Jenkins jobs are configured to use the CI server's temmpo user account's SSH keys /usr/local/projects/temmpo/.ssh/id_rsa.pub and the rit-temmpo-ci Bitbucket user's SSH key.

### To build a demo Python virtual environment from the CI server

*One off setup*

    ssh ci-p0.rit.bris.ac.uk
    sudo -i -u temmpo
    cd /srv/projects/temmpo/lib/git/temmpo/
    git fetch origin
    git checkout master
    git pull
    fab make_virtualenv:env=demo,configure_apache=True,clone_repo=True,branch=demo_stable,migrate_db=True,use_local_mode=False,requirements=base -u temmpo -i /usr/local/projects/temmpo/.ssh/id_rsa.pub -H py-web-d0.epi.bris.ac.uk -f /srv/projects/temmpo/lib/git/temmpo/deploy/fabfile.py

## Testing environment

### Testing changes on the master branch on the test environment https://py-web-t0.epi.bris.ac.uk/

The Research IT Jenkins continuous integration server is used to automate running tests.  Periodically changes that have been moved onto the master branch will be deployed onto the test server.  See: https://ci-p0.rit.bris.ac.uk/job/TeMMPo/job/Test%20jobs/job/1-run-tests/

Below are the shell commands that each part of the CI pipeline runs from the CI server ci-p0.rit.bris.ac.uk:

1. Project 1-run-tests

        # Build test environment
        fab make_virtualenv:env=test,configure_apache=True,clone_repo=True,branch=master,migrate_db=False,use_local_mode=False,requirements=test -u temmpo -H py-web-t0.epi.bris.ac.uk -f deploy/fabfile.py --forward-agent
        # Clear database
        fab recreate_db:env=test,database_name=temmpo_test -u temmpo -H py-web-t0.epi.bris.ac.uk -f deploy/fabfile.py --forward-agent
        # Run tests
        fab run_tests:env=test,use_local_mode=False,reuse_db=True,db_type=mysql,run_selenium_tests=True -u temmpo -H py-web-t0.epi.bris.ac.uk -f deploy/fabfile.py --forward-agent

2. Project 2-update-last-known-good-branch

        if [ ! -d temmpo ] ; then git clone git@bitbucket.org:researchit/temmpo.git; fi
        cd temmpo
        git fetch origin
        git checkout master 
        git pull
        git checkout last_known_good
        git pull
        git merge -m "RIT Jenkins CI merged master into last_known_good branch after tests passed on Centos test server" master
        git push origin last_known_good

NB: The Jenkins jobs are configured to use the CI server's temmpo user account's SSH keys /usr/local/projects/temmpo/.ssh/id_rsa.pub and the rit-temmpo-ci Bitbucket user's SSH key.

### To build a test Python virtual environment, run the below commands from the CI server

*One off setup*

    ssh ci-p0.rit.bris.ac.uk
    sudo -i -u temmpo
    cd /srv/projects/temmpo/lib/git/temmpo/
    git fetch origin
    git checkout master
    git pull
    fab make_virtualenv:env=test,configure_apache=True,clone_repo=True,branch=master,migrate_db=False,use_local_mode=False,requirements=base -u temmpo -i /usr/local/projects/temmpo/.ssh/id_rsa.pub -H py-web-t0.epi.bris.ac.uk -f /srv/projects/temmpo/lib/git/temmpo/deploy/fabfile.py

## Setting up a new host 

- To be able to provision the Django application using the Fabric script from the CI server you will need the following to be in place.

1. Ensure the project specific puppet configuration https://gitlab.isys.bris.ac.uk/research_it/temmpo has been updated for and run on the new host.  NB This should run all the environment specific steps provided in the development Vagrant file and set up scripts.

2. Create a /usr/local/projects/temmpo/.settings/private_settings.py file, see example_private_settings.py file for expected format and entries.

3. Share the SSH key for the temmpo user from the CI server ci-p0.rit.bris.ac.uk to the new host.

4. Create and add a new SSH deployment key to the Bitbucket code repository

5. Ensure an 'env'.py file exists, e.g. demo.py, prod.py, in the code's *temmpo/temmpo/settings* directory.

6. Build new Python virtual environment, see steps for building production, demo or test for example commands.

## Warnings

    IntegrityError at /search/ovidmedline/
    (1048, "Column 'mesh_terms_year_of_release' cannot be null")

This suggests attempting to create a search when no mesh terms have been imported.

## Debugging issues

The project needs the following additional services to be running:

    sudo systemctl status redis
    sudo systemctl status rqworker
    sudo systemctl status httpd      # Not relevant for the django Vagrant VM


