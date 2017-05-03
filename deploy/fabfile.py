from datetime import datetime
import os

from fabric.api import *
from fabric.contrib import files

PROJECT_ROOT = "/usr/local/projects/temmpo/"
GIT_DIR = "/usr/local/projects/temmpo/lib/git/"
GIT_URL = 'git@bitbucket.org:researchit/temmpo.git'
PIP_VERSION = '9.0.1'
# SETUPTOOLS_VERSION = '34.4.1'
GIT_SSH_HOSTS = ('104.192.143.1',
                 '104.192.143.2',
                 '104.192.143.3',
                 'bitbucket.org',)


def _add_file_local(path, contents, use_local_mode):
    if use_local_mode:
        with open(path, 'w') as f:
            f.write(contents)
    else:
        files.append(path, contents, partial=True)


def _exists_local(path, use_local_mode):
    if use_local_mode:
        return os.path.exists(path)
    else:
        return files.exists(path)


def _is_link_local(path, use_local_mode):
    if use_local_mode:
        return os.path.islink(path)
    else:
        return files.is_link(path)


def _toggle_local_remote(use_local_mode):
    if use_local_mode:
        caller = local
        change_dir = lcd
    else:
        caller = run
        change_dir = cd

    return (caller, change_dir)


def taggit(gfrom='master', gto='', egg='', msg='Marking for release'):
    """fab:master,0.9,egg Create a tag or move a branch
        Example create a tag and move it to stable...
        taggit:master,0.8 then taggit:master,prod_stable
    """
    if not (gfrom and gto and egg):
        print 'You must specify taggit:from,to,egg'
        return
    try:
        testint = int(gfrom[0])
        print 'Don\'t move numeric tags please - add a new one!'
        return
    except:
        pass
    try:
        testint = int(gto[0])
        print 'Marking release tag %s on branch %s' % (gto, gfrom)
        action = 'tag'
    except:
        print 'Merging branch %s to branch %s' % (gto, gfrom)
        action = 'merge'
    with lcd(GIT_DIR + egg):
        local('git pull')
        if action == 'merge':
            # make sure this is up to date branches before merging
            local('git checkout %s' % gfrom)
            local('git pull')
            local('git checkout %s' % gto)
            local('git pull')
            local('git merge -m "merge for release tagging" %s' % gfrom)
            local('git push')
        else:
            local('git checkout %s' % gfrom)
            local('git tag -a %s -m "%s"' % (gto, msg))
            local('git push origin %s' % gto)
        # Reset local git repo to master
        local('git checkout master')


def make_virtualenv(env="dev", configure_apache=False, clone_repo=False, branch=None, migrate_db=True, use_local_mode=False, requirements="base"):
    """NB: env = dev|prod, configure_apache=False, clone_repo=False, branch=None, migrate_db=True, use_local_mode=False, requirements="base"""
    # Convert any string command line arguments to boolean values, where required.
    configure_apache = (str(configure_apache).lower() == 'true')
    clone_repo = (str(clone_repo).lower() == 'true')
    migrate_db = (str(migrate_db).lower() == 'true')
    use_local_mode = (str(use_local_mode).lower() == 'true')

    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    src_dir = PROJECT_ROOT + "lib/" + env + "/src/"
    venv_dir = PROJECT_ROOT + "lib/" + env + "/"

    # Create application specific directories
    caller('mkdir -p %svar/results' % PROJECT_ROOT)
    caller('mkdir -p %svar/abstracts' % PROJECT_ROOT)

    with change_dir(PROJECT_ROOT + 'lib/'):
        caller('virtualenv %s' % env)

        if clone_repo:
            caller('mkdir -p %s' % src_dir)
            # TODO Improve so the known_hosts file does not keep growing
            for host in GIT_SSH_HOSTS:
                caller('ssh-keyscan -H %s >> ~/.ssh/known_hosts' % host)
            if not _exists_local(src_dir + "/temmpo", use_local_mode):
                with change_dir(src_dir):
                    caller('git clone %s temmpo' % GIT_URL)
            with change_dir(src_dir + "/temmpo"):
                caller('git fetch --all')
                caller('git fetch origin %s' % branch)
                caller('git checkout %s' % branch)
                caller('git pull')

        with change_dir(venv_dir):
            caller('./bin/pip install -U pip==%s' % PIP_VERSION)
            # caller('./bin/pip install -U setuptools==%s' % SETUPTOOLS_VERSION)
            caller('./bin/pip install -r src/temmpo/requirements/%s.txt' % requirements)

        sym_link_private_settings(env, use_local_mode)

    # Set up logging
    if not _exists_local(PROJECT_ROOT + 'var/log/django.log', use_local_mode):
        caller('mkdir -p ' + PROJECT_ROOT + 'var/log/')
        caller('touch %svar/log/django.log' % PROJECT_ROOT)

    if migrate_db:
        with change_dir(PROJECT_ROOT + 'lib/' + env):
            caller('./bin/python src/temmpo/manage.py migrate --database=admin --noinput --settings=temmpo.settings.%s' % env)

    if configure_apache:
        collect_static(env, use_local_mode)
        setup_apache(env, use_local_mode)


def deploy(env="dev", branch="master", using_apache=True, tag='', merge_from='', migrate_db=True, use_local_mode=False, use_pip_sync=False, requirements="base"):
    """NB: env = dev|prod.  Optionally tag and merge the release env="dev", branch="master", using_apache=True, tag='', merge_from='', migrate_db=True, use_local_mode=False, use_pip_sync=False, requirements="base"
    TODO: Tagging and merging branches needs testing"""

    # Convert any string command line arguments to boolean values, where required.
    using_apache = (str(using_apache).lower() == 'true')
    migrate_db = (str(migrate_db).lower() == 'true')
    use_local_mode = (str(use_local_mode).lower() == 'true')
    use_pip_sync = (str(use_pip_sync).lower() == 'true')

    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = PROJECT_ROOT + "lib/" + env + "/"

    if using_apache:
        disable_apache_site(use_local_mode)

    if tag:
        taggit(gfrom="master", gto=tag, egg='temmpo')

    if merge_from:
        taggit(gfrom=merge_from, gto=branch, egg='temmpo')

    src_dir = PROJECT_ROOT + "lib/" + env + "/src/temmpo/"

    with cd(src_dir):
        caller('git fetch --all')
        caller('git fetch origin %s' % branch)
        caller('git checkout %s' % branch)
        caller('git pull origin %s' % branch)

    with change_dir(venv_dir):
        if use_pip_sync:
            caller('./bin/pip-sync src/temmpo/requirements/%s.txt' % requirements)
        else:
            caller('./bin/pip install -r src/temmpo/requirements/%s.txt' % requirements)

        if migrate_db:
            caller('./bin/python src/temmpo/manage.py migrate --database=admin --settings=temmpo.settings.%s' % env)

        if using_apache:
            collect_static(env, use_local_mode)
            restart_apache(env, use_local_mode, run_checks=True)
            enable_apache_site(use_local_mode)


def setup_apache(env="dev", use_local_mode=False):
    # env="dev", use_local_mode=False Convert any string command line arguments to boolean values, where required.
    use_local_mode = (str(use_local_mode).lower() == 'true')

    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)

    venv_dir = PROJECT_ROOT + "lib/" + env + "/"
    src_dir = venv_dir + "src/"
    var_dir = PROJECT_ROOT + 'var/'
    static_dir = PROJECT_ROOT + 'var/www/static'

    apache_conf_file = PROJECT_ROOT + 'etc/apache/conf.d/temmpo.conf'

    if _exists_local(apache_conf_file, use_local_mode):
        caller("rm %s" % apache_conf_file)

    apache_conf = """
    WSGIScriptAlias / /usr/local/projects/temmpo/lib/%(env)s/src/temmpo/temmpo/wsgi.py
    # WSGIApplicationGroup %%{GLOBAL}
    # WSGIDaemonProcess temmpo
    # WSGIProcessGroup temmpo

    RewriteEngine On
    RewriteCond %%{DOCUMENT_ROOT}/_MAINTENANCE_ -f
    RewriteCond %%{REQUEST_URI} !/static/maintenance/maintenance.html
    RewriteRule ^(.+) /static/maintenance/maintenance.html [R,L]

    <Directory /usr/local/projects/temmpo/lib/%(env)s/src/temmpo>
        Require all granted
    </Directory>

    <Directory /usr/local/projects/temmpo/lib/%(env)s/lib>
        Require all granted
    </Directory>

    <Directory /usr/local/projects/temmpo/lib/%(env)s/src/temmpo/temmpo>
        <Files wsgi.py>
            Require all granted
        </Files>
    </Directory>

    <Directory /usr/local/projects/temmpo/var/www/static>
        Require all granted
    </Directory>

    Alias /static/ "/usr/local/projects/temmpo/var/www/static/"

    <Location "/static">
        SetHandler None
    </Location>""" % {'env': env}

    _add_file_local(apache_conf_file, apache_conf, use_local_mode)

    # Set up static directory
    caller("mkdir -p %s" % static_dir)

    # Set up SE Linux contexts
    caller('chcon -R -t httpd_sys_content_t %s' % static_dir)   # Only needs to be readable
    caller('chcon -R -t httpd_sys_script_exec_t %slib/python2.7/' % venv_dir)
    caller('chcon -R -t httpd_sys_script_exec_t %s' % src_dir)
    # caller('chcon -R -t httpd_sys_script_exec_t %s.settings' % PROJECT_ROOT)
    caller('chcon -R -t httpd_sys_rw_content_t %slog/django.log' % var_dir)

    restart_apache(env, use_local_mode, run_checks=True)


def collect_static(env="dev", use_local_mode=False):
    """Gather static files to be served by Apache"""

    # Convert any string command line arguments to boolean values, where required.
    use_local_mode = (str(use_local_mode).lower() == 'true')

    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = PROJECT_ROOT + "lib/" + env

    with change_dir(venv_dir):
        caller('./bin/python src/temmpo/manage.py collectstatic --noinput --settings=temmpo.settings.%s' % env)


def restart_apache(env="dev", use_local_mode=False, run_checks=True):
    """ env="dev", use_local_mode=False, run_checks=True"""
    # Convert any string command line arguments to boolean values, where required.
    use_local_mode = (str(use_local_mode).lower() == 'true')
    run_checks = (str(run_checks).lower() == 'true')
    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = PROJECT_ROOT + "lib/" + env + "/"

    caller("sudo /sbin/apachectl configtest")
    caller("sudo /sbin/apachectl restart")
    caller("sudo /sbin/apachectl status")
    if run_checks:
        toggled_maintenance_mode = False
        if _exists_local(PROJECT_ROOT + "var/www/_MAINTENANCE_", use_local_mode):
            toggled_maintenance_mode = True
            enable_apache_site(use_local_mode)
            print "Enable!!!!!!!!!!!!!!!!!!"

        caller("wget 127.0.0.1")
        caller("rm index.html")
        with change_dir(venv_dir):
            caller("./bin/python src/temmpo/manage.py check --deploy --settings=temmpo.settings.%s" % env)

        if toggled_maintenance_mode:
            disable_apache_site(use_local_mode)


def migrate_sqlite_data_to_mysql(env="dev", use_local_mode=False, using_apache=True, swap_db=True):
    """env="dev", use_local_mode=False, using_apache=True, swap_db=True - NB: Written to migrate the data once, not to drop any existing MySQL tables;"""
    use_local_mode = (str(use_local_mode).lower() == 'true')
    using_apache = (str(using_apache).lower() == 'true')
    swap_db = (str(swap_db).lower() == 'true')
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = PROJECT_ROOT + "lib/" + env + "/"
    now = datetime.now()
    date_string = "%s-%s-%s-%s-%s" % (now.year, now.month, now.day, now.hour, now.minute)
    sqlite_db = '/usr/local/projects/temmpo/var/data/db.sqlite3'
    output_file = "/usr/local/projects/temmpo/var/data/export-db-%s.sql" % date_string
    sqlite_table_counts_file = "/usr/local/projects/temmpo/var/data/sqlite-counts-%s.txt" % date_string
    mysql_table_counts_file = "/usr/local/projects/temmpo/var/data/mysql-counts-%s.txt" % date_string
    sqlite_status_file = "/usr/local/projects/temmpo/var/data/sqlite-status-%s.txt" % date_string
    mysql_status_file = "/usr/local/projects/temmpo/var/data/mysql-status-%s.txt" % date_string
    tables = ('auth_group',
              'browser_searchcriteria_genes',
              'auth_group_permissions',
              'browser_searchcriteria_mediator_terms',
              'auth_permission',
              'browser_searchcriteria_outcome_terms',
              'auth_user',
              'browser_searchresult',
              'auth_user_groups',
              'browser_upload',
              'auth_user_user_permissions',
              'django_admin_log',
              'browser_abstract',
              'django_content_type',
              'browser_gene',
              'django_migrations',
              'browser_meshterm',
              'django_session',
              'browser_searchcriteria',
              'registration_registrationprofile',)
    compare_data = ''
    for table in tables:
        compare_data += "SELECT count(*) FROM %s; " % table

    compare_sqlite = ".tables"
    compare_mysql = "SHOW TABLES"

    if using_apache:
        disable_apache_site(use_local_mode)

    with change_dir(venv_dir):
        # Export data - NB: No drop table commands are included in this dump
        caller("sqlite3 %s .dump > %s" % (sqlite_db, output_file))
        # Export comparison from SQLite
        caller("sqlite3 %s '%s' > %s" % (sqlite_db, compare_data, sqlite_table_counts_file))
        caller("echo '%s' | ./bin/python src/temmpo/manage.py dbshell --settings=temmpo.settings.%s --database=sqlite > %s" % (compare_sqlite, env, sqlite_status_file))
        # Convert certain commands from SQLite to the MySQL equivalents
        caller("sed -i -e 's/PRAGMA.*/SET SESSION sql_mode = ANSI_QUOTES;/' -e 's/BEGIN/START/' -e 's/AUTOINCREMENT/AUTO_INCREMENT/g' -e 's/^.*sqlite_sequence.*$//g' %s" % output_file)
        # Import data
        caller("cat %s | ./bin/python src/temmpo/manage.py dbshell --settings=temmpo.settings.%s --database=admin" % (output_file, env))
        # Export comparison data from MySQL
        caller("echo '%s' | ./bin/python src/temmpo/manage.py dbshell --settings=temmpo.settings.%s --database=mysql  > %s" % (compare_mysql, env, mysql_status_file))
        caller("echo '%s' | ./bin/python src/temmpo/manage.py dbshell --settings=temmpo.settings.%s --database=mysql  > %s" % (compare_data, env, mysql_table_counts_file))
        # Trim header of MySQL output file
        caller("sed -i 1,1d %s " % mysql_status_file)
        # Trim output headers from MySQL table counts
        caller("sed -i 1,1d %s " % mysql_table_counts_file)
        caller("sed -i -e 's/count(\*)//g' %s" % mysql_table_counts_file)
        caller("tr --squeeze-repeats '\\n' < %s > tmp.txt && mv tmp.txt %s" % (mysql_table_counts_file, mysql_table_counts_file))
        # Trim trailing white space
        caller("sed -i -e 's/ \{1,\}$//g' %s" % sqlite_status_file)
        # Split into one column
        caller("sed -i -e 's/ \{1,\}/\\n/g' %s" % sqlite_status_file)
        caller("sort %s -o %s" % (sqlite_status_file, sqlite_status_file))
        caller("diff %s %s" % (sqlite_status_file, mysql_status_file))
        caller("diff %s %s" % (sqlite_table_counts_file, mysql_table_counts_file))

    if swap_db:
        with change_dir(PROJECT_ROOT):
            # Update database default
            caller("echo -e '\nDATABASES[\"default\"] = DATABASES[\"mysql\"]' >> .settings/private_settings.py")
            # Move SQLite DB to one side
            caller("mv %s %s-old" % (sqlite_db, sqlite_db))

    if using_apache:
        enable_apache_site(use_local_mode)
        restart_apache(env, use_local_mode, run_checks=True)


def sym_link_private_settings(env="dev", use_local_mode=False):
    """env="dev", use_local_mode=False"""
    use_local_mode = (str(use_local_mode).lower() == 'true')
    caller, change_dir = _toggle_local_remote(use_local_mode)

    private_settings_sym_link = '%slib/%s/src/temmpo/temmpo/settings/private_settings.py' % (PROJECT_ROOT, env)
    if not _is_link_local(private_settings_sym_link, use_local_mode):
        caller('ln -s %s.settings/private_settings.py %s' % (PROJECT_ROOT, private_settings_sym_link))


def disable_apache_site(use_local_mode=False):
    """use_local_mode=False"""
    _toggle_maintenance_mode("_MAINTENANCE_OFF", "_MAINTENANCE_", use_local_mode=False)


def enable_apache_site(use_local_mode=False):
    """use_local_mode=False"""
    _toggle_maintenance_mode("_MAINTENANCE_", "_MAINTENANCE_OFF", use_local_mode=False)


def _toggle_maintenance_mode(old_flag, new_flag, use_local_mode=False):
    """old_flag, new_flag, use_local_mode=False"""
    use_local_mode = (str(use_local_mode).lower() == 'true')
    caller, change_dir = _toggle_local_remote(use_local_mode)

    with change_dir(PROJECT_ROOT + 'var/www/'):
        caller("rm -f %s" % old_flag)
        caller("touch %s" % new_flag)
