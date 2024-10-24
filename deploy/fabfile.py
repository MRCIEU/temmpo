"""Fabric script used in CI and CD pipeline."""

# TODO: See: https://www.fabfile.org/upgrading.html#upgrading


from datetime import datetime
import os
from urllib.request import urlopen

from fabric.api import *
from fabric.contrib import files

PROJECT_ROOT = "/usr/local/projects/temmpo/"

GIT_URL = 'git@github.com:MRCIEU/temmpo.git'
GIT_SSH_HOSTS = ('bitbucket.org',
                 'github.com',)

# Tools not handled by pip-tools and/or requirements installs using pip
# Also update pip version in tests/build-test-env.sh and Dockerfile
PIP_VERSION = '24.2'
SETUPTOOLS_VERSION = '74.1.2'
PIP_TOOLS_VERSION = '7.4.1'


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


def make_virtualenv(env="dev", configure_apache=False, clone_repo=False, branch=None, migrate_db=True, use_local_mode=False, requirements="requirements", restart_rqworker=True, virtualenv="virtualenv-3.8", project_dir=PROJECT_ROOT):
    """NB: env = dev|prod, configure_apache=False, clone_repo=False, branch=None, migrate_db=True, use_local_mode=False, requirements="requirements"."""
    # Convert any string command line arguments to boolean values, where required.
    configure_apache = (str(configure_apache).lower() == 'true')
    clone_repo = (str(clone_repo).lower() == 'true')
    migrate_db = (str(migrate_db).lower() == 'true')
    use_local_mode = (str(use_local_mode).lower() == 'true')
    restart_rqworker = (str(restart_rqworker).lower() == 'true')

    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    src_dir = project_dir + "lib/" + env + "/src/"
    venv_dir = project_dir + "lib/" + env + "/"

    # Create application specific directories
    caller('mkdir -p %svar/results/v1' % project_dir)
    caller('mkdir -p %svar/results/v3' % project_dir)
    caller('mkdir -p %svar/results/v4' % project_dir)
    caller('mkdir -p %svar/abstracts' % project_dir)

    if configure_apache:
        disable_apache_site(use_local_mode)
    if restart_rqworker:
        stop_rqworker_service(use_local_mode)

    with change_dir(project_dir + 'lib/'):
        caller('%s --python python3.8 %s' % (virtualenv, env))
        # Verify Python version in use
        caller('%s/bin/python3 -V' % env)

        if clone_repo:
            caller('mkdir -p %s' % src_dir)
            # TODO: (Low priority) Improve so the known_hosts file does not keep growing
            for host in GIT_SSH_HOSTS:
                caller('ssh-keyscan -H %s >> ~/.ssh/known_hosts' % host)
            if not _exists_local(src_dir + "temmpo", use_local_mode):
                with change_dir(src_dir):
                    caller('git clone %s temmpo' % GIT_URL)
            with change_dir(src_dir + "temmpo"):
                # Remove any Python 2 cached files
                caller('rm -f `find . -type d \( -name __pycache__ -o -path name \) -prune -false -o -name *.pyc`')
                # Alternatively Remove all cache file -  find . -type f -name "*.py[co]" -delete -or -type d -name "__pycache__" -delete
                # Ensure file mode changes do not trigger changes that can block a git pull command
                caller('git config core.fileMode false')
                caller('git fetch --all')
                caller('git fetch origin %s' % branch)
                caller('git checkout %s' % branch)
                caller('git pull')

        with change_dir(venv_dir):
            caller('./bin/pip3 -V')
            caller('./bin/pip3 install --force-reinstall -U pip==%s' % PIP_VERSION)
            caller('./bin/pip3 cache purge')
            caller('./bin/pip3 install -U setuptools==%s' % SETUPTOOLS_VERSION)
            caller('./bin/pip3 install pip-tools==%s' % PIP_TOOLS_VERSION)
            # Fix TMMA-456 - Resolve issue on Debian systems where dependencies loosely pinned upstream but correctly pinned overall in our requirements file causes builds to fail
            caller('./bin/pip3 install --no-deps --require-hashes -r src/temmpo/requirements/%s.txt' % requirements)
            caller('./bin/pip3 freeze')
            
            # # Regenerate all pyc files
            # caller('./bin/python3 src/temmpo/manage.py regenerate_pyc --settings=temmpo.settings.%s' % env)

        # TMMA-426: Update deployment scripts to remove any .exe files from pip environment
        caller('find . -name *.exe | xargs rm -f')

        sym_link_private_settings(env, use_local_mode, project_dir)

    # Set up logging
    if not _exists_local(project_dir + 'var/log/django.log', use_local_mode):
        caller('mkdir -p ' + project_dir + 'var/log/')
        caller('touch %svar/log/django.log' % project_dir)

    if migrate_db:
        with change_dir(project_dir + 'lib/' + env):
            caller('./bin/python3 src/temmpo/manage.py migrate --database=admin --noinput --settings=temmpo.settings.%s' % env)

    if configure_apache:
        collect_static(env, use_local_mode)
        setup_apache(env, use_local_mode)
        enable_apache_site(use_local_mode)

    if restart_rqworker:
        start_rqworker_service(use_local_mode)


def deploy(env="dev", branch="master", using_apache=True, migrate_db=True, use_local_mode=False, use_pip_sync=False, requirements="requirements", project_dir=PROJECT_ROOT):
    """NB: env = dev|prod.  Optionally tag and merge the release env="dev", branch="master", using_apache=True, migrate_db=True, use_local_mode=False, use_pip_sync=False, requirements="requirements"."""
    # Convert any string command line arguments to boolean values, where required.
    using_apache = (str(using_apache).lower() == 'true')
    migrate_db = (str(migrate_db).lower() == 'true')
    use_local_mode = (str(use_local_mode).lower() == 'true')
    use_pip_sync = (str(use_pip_sync).lower() == 'true')

    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = project_dir + "lib/" + env + "/"

    if using_apache:
        disable_apache_site(use_local_mode)
    stop_rqworker_service(use_local_mode)

    src_dir = project_dir + "lib/" + env + "/src/temmpo/"

    with cd(src_dir):
        # Remove any cached python project files
        caller('rm -f `find . -type d \( -name __pycache__ -o -path name \) -prune -false -o -name *.pyc`')
        # Ensure file mode changes do not trigger changes that can block a git pull command
        caller('git config core.fileMode false')
        caller('git fetch --all')
        caller('git fetch origin %s' % branch)
        caller('git checkout %s' % branch)
        caller('git pull origin %s' % branch)

    with change_dir(venv_dir):

        # Remove any python dependency pyc files
        caller('rm -f `find lib/python3.8/site-packages/ -type d \( -name __pycache__ -o -path name \) -prune -false -o -name *.pyc`')

        # Ensure pip3 and setup tools is up to expected version for existing environments.
        caller('./bin/pip3 cache purge')
        caller('./bin/pip3 install -U pip==%s' % PIP_VERSION)
        caller('./bin/pip3 install -U setuptools==%s' % SETUPTOOLS_VERSION)
        caller('./bin/pip3 install pip-tools==%s' % PIP_TOOLS_VERSION)

        if use_pip_sync:
            caller('./bin/pip-sync src/temmpo/requirements/%s.txt' % requirements)
        else:
            caller('./bin/pip3 install -r src/temmpo/requirements/%s.txt' % requirements)

        # # Regenerate all pyc files
        # caller('./bin/python3 src/temmpo/manage.py regenerate_pyc --settings=temmpo.settings.%s' % env)

        if migrate_db:
            caller('./bin/python3 src/temmpo/manage.py migrate --noinput --database=admin --settings=temmpo.settings.%s' % env)

        if using_apache:
            collect_static(env, use_local_mode)
            setup_apache(env, use_local_mode)
            restart_apache(env, use_local_mode, run_checks=True)
            enable_apache_site(use_local_mode)

    start_rqworker_service(use_local_mode)

def setup_apache(env="dev", use_local_mode=False, project_dir=PROJECT_ROOT):
    """env="dev", use_local_mode=False Convert any string command line arguments to boolean values, where required."""
    use_local_mode = (str(use_local_mode).lower() == 'true')

    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)

    venv_dir = project_dir + "lib/" + env + "/"
    src_dir = venv_dir + "src/"
    var_dir = project_dir + 'var/'
    static_dir = project_dir + 'var/www/static'

    apache_conf_file = project_dir + 'etc/apache/conf.d/temmpo.conf'

    if _exists_local(apache_conf_file, use_local_mode):
        caller("rm %s" % apache_conf_file)

    apache_conf = """
    Header set X-Frame-Options "DENY"
    TraceEnable off

    WSGIScriptAlias / /usr/local/projects/temmpo/lib/%(env)s/src/temmpo/temmpo/wsgi.py
    # WSGIPythonHome /usr/local/projects/temmpo/bin/python3
    # WSGIPythonPath /usr/local/projects/temmpo/lib/%(env)s/src
    # WSGIApplicationGroup %%{GLOBAL}
    # WSGIDaemonProcess temmpo
    # WSGIProcessGroup temmpo

    RewriteEngine On
    RewriteCond %%{DOCUMENT_ROOT}/_MAINTENANCE_ -f
    RewriteCond %%{REQUEST_URI} !/static/(.*)$
    RewriteRule ^(.+) /static/maintenance/maintenance.html [R=302,L]

    RewriteCond %%{HTTP_HOST} ^temmpo.org.uk$ [NC]
    RewriteRule ^(.+) https://www.temmpo.org.uk$1 [R=301,L]

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
        Options -Indexes
        Require all granted
    </Directory>

    Alias /static/ "/usr/local/projects/temmpo/var/www/static/"
    Alias /media/abstracts/ "/usr/local/projects/temmpo/var/abstracts/"
    Alias /media/results/ "/usr/local/projects/temmpo/var/results/"

    <Location "/static">
        SetHandler None
        AllowMethods GET
    </Location>

    <Location "/media/abstracts">
        SetHandler None
        AllowMethods GET
    </Location>

    <Location "/media/results">
        SetHandler None
        AllowMethods GET
    </Location>

    <LocationMatch "^/(admin|django-rq)">
        Require ip 137.222
        Require ip 10.0.0.0/8
        Require ip 172.16.0.0/12
        Require ip 192.168.0.0/16
    </LocationMatch>

    """ % {'env': env}

    _add_file_local(apache_conf_file, apache_conf, use_local_mode)

    # Set up static directory
    caller("mkdir -p %s" % static_dir)

    if env == "dev":
        # Set up SE Linux contexts for dev environments, puppet configured for VMs
        caller('chcon -R -t httpd_sys_content_t %s' % static_dir)   # Only needs to be readable
        caller('chcon -R -t httpd_sys_script_exec_t %slib/python3.8/' % venv_dir)
        caller('chcon -R -t httpd_sys_script_exec_t %s' % src_dir)
        # caller('chcon -R -t httpd_sys_script_exec_t %s.settings' % PROJECT_ROOT)
        caller('chcon -R -t httpd_sys_rw_content_t %slog/django.log' % var_dir)

    restart_apache(env, use_local_mode, run_checks=True)


def collect_static(env="dev", use_local_mode=False, project_dir=PROJECT_ROOT):
    """Gather static files to be served by Apache."""
    # Convert any string command line arguments to boolean values, where required.
    use_local_mode = (str(use_local_mode).lower() == 'true')

    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = project_dir + "lib/" + env

    with change_dir(venv_dir):
        caller('./bin/python3 src/temmpo/manage.py collectstatic --noinput --settings=temmpo.settings.%s' % env)


def restart_apache(env="dev", use_local_mode=False, run_checks=True, project_dir=PROJECT_ROOT):
    """env="dev", use_local_mode=False, run_checks=True."""
    # Convert any string command line arguments to boolean values, where required.
    use_local_mode = (str(use_local_mode).lower() == 'true')
    run_checks = (str(run_checks).lower() == 'true')
    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = project_dir + "lib/" + env + "/"

    caller("sudo /sbin/apachectl configtest")
    caller("sudo /sbin/apachectl restart")
    # Commented to disable.
    # Unfortunately, on RHEL 8, this pipes into `less` and that then waits for
    # user input to continue (as `less` is paging the long-line output of
    # apachectl status). As there's no practical way to pass `--no-pager` to
    # the systemctl status call that underlies the apachectl call, skip it for
    # the time being.
    # TODO: Either stop this being paged or switch to `systemctl` calls
    # directly to allow for passing `--no-pager`.
    # caller("sudo /sbin/apachectl status")
    if run_checks:
        toggled_maintenance_mode = False
        if _exists_local(project_dir + "var/www/_MAINTENANCE_", use_local_mode):
            toggled_maintenance_mode = True
            enable_apache_site(use_local_mode)

        caller("wget --timeout=60 --tries=1 127.0.0.1")
        caller("rm index.html")
        with change_dir(venv_dir):
            caller("./bin/python3 src/temmpo/manage.py check --deploy --settings=temmpo.settings.%s" % env)

        if toggled_maintenance_mode:
            disable_apache_site(use_local_mode)


def migrate_sqlite_data_to_mysql(env="dev", use_local_mode=False, using_apache=True, swap_db=True, project_dir=PROJECT_ROOT):
    """env="dev", use_local_mode=False, using_apache=True, swap_db=True - NB: Written to migrate the data once, not to drop any existing MySQL tables."""
    use_local_mode = (str(use_local_mode).lower() == 'true')
    using_apache = (str(using_apache).lower() == 'true')
    swap_db = (str(swap_db).lower() == 'true')
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = project_dir + "lib/" + env + "/"
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
        caller("echo '%s' | ./bin/python3 src/temmpo/manage.py dbshell --settings=temmpo.settings.%s --database=sqlite > %s" % (compare_sqlite, env, sqlite_status_file))
        # Convert certain commands from SQLite to the MySQL equivalents
        caller("sed -i -e 's/PRAGMA.*/SET SESSION sql_mode = ANSI_QUOTES;/' -e 's/BEGIN/START/' -e 's/AUTOINCREMENT/AUTO_INCREMENT/g' -e 's/^.*sqlite_sequence.*$//g' %s" % output_file)
        # Import data
        caller("cat %s | ./bin/python3 src/temmpo/manage.py dbshell --settings=temmpo.settings.%s --database=admin" % (output_file, env))
        # Export comparison data from MySQL
        caller("echo '%s' | ./bin/python3 src/temmpo/manage.py dbshell --settings=temmpo.settings.%s --database=mysql  > %s" % (compare_mysql, env, mysql_status_file))
        caller("echo '%s' | ./bin/python3 src/temmpo/manage.py dbshell --settings=temmpo.settings.%s --database=mysql  > %s" % (compare_data, env, mysql_table_counts_file))
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


def sym_link_private_settings(env="dev", use_local_mode=False, project_dir=PROJECT_ROOT):
    """env="dev", use_local_mode=False."""
    use_local_mode = (str(use_local_mode).lower() == 'true')
    caller, change_dir = _toggle_local_remote(use_local_mode)

    private_settings_sym_link = '%slib/%s/src/temmpo/temmpo/settings/private_settings.py' % (project_dir, env)
    if not _is_link_local(private_settings_sym_link, use_local_mode):
        caller('ln -s %s.settings/private_settings.py %s' % (PROJECT_ROOT, private_settings_sym_link))


def disable_apache_site(use_local_mode=False):
    """use_local_mode=False."""
    _toggle_maintenance_mode("_MAINTENANCE_OFF", "_MAINTENANCE_", use_local_mode=False)


def enable_apache_site(use_local_mode=False):
    """use_local_mode=False."""
    _toggle_maintenance_mode("_MAINTENANCE_", "_MAINTENANCE_OFF", use_local_mode=False)


def _toggle_maintenance_mode(old_flag, new_flag, use_local_mode=False, project_dir=PROJECT_ROOT):
    """old_flag, new_flag, use_local_mode=False."""
    use_local_mode = (str(use_local_mode).lower() == 'true')
    caller, change_dir = _toggle_local_remote(use_local_mode)

    with change_dir(project_dir + 'var/www/'):
        caller("rm -f %s" % old_flag)
        caller("touch %s" % new_flag)

def _change_rqworker_service(use_local_mode, action):
    caller, change_dir = _toggle_local_remote(use_local_mode)
    for num in range(1, 5):
        caller("sudo service rqworker%d %s" % (num, action))

def restart_rqworker_service(use_local_mode):
    _change_rqworker_service(use_local_mode, action="stop")
    _change_rqworker_service(use_local_mode, action="start")

def stop_rqworker_service(use_local_mode):
    _change_rqworker_service(use_local_mode, action="stop")

def start_rqworker_service(use_local_mode):
    _change_rqworker_service(use_local_mode, action="start")

def run_tests(env="test", use_local_mode=False, reuse_db=False, db_type="mysql", run_selenium_tests=False, tag=None, exclude_tag=None, project_dir=PROJECT_ROOT):
    """env=test,use_local_mode=False,reuse_db=False,db_type=mysql,run_selenium_tests=False,tag=None"""
    # Convert any command line arguments from strings to boolean values where necessary.
    use_local_mode = (str(use_local_mode).lower() == 'true')
    reuse_db = (str(reuse_db).lower() == 'true')
    run_selenium_tests = (str(run_selenium_tests).lower() == 'true')
    cmd_suffix = ''
    if reuse_db:
        cmd_suffix = " --keepdb"
    if exclude_tag and exclude_tag != "None":
        cmd_suffix += " --exclude-tag=%s" % exclude_tag
    if tag and tag != "None":
        cmd_suffix += " --tag=%s" % tag
    if not run_selenium_tests:
        cmd_suffix += " --exclude-tag=selenium-test"
    elif tag and tag != "None":
        cmd_suffix += " --tag=selenium-test"

    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = project_dir + "lib/" + env + "/"
    src_dir = project_dir + "lib/" + env + "/src/temmpo/"

    with change_dir(src_dir):
        caller('%sbin/python3 manage.py test --noinput --exclude-tag=slow %s --settings=temmpo.settings.test_%s' % (venv_dir, cmd_suffix, db_type))

def run_slow_tests(env="test", use_local_mode=False, reuse_db=False, db_type="mysql", run_selenium_tests=False, tag=None, project_dir=PROJECT_ROOT):
    """env=test,use_local_mode=False,reuse_db=False,db_type=mysql,run_selenium_tests=False,tag=None"""
    # Convert any command line arguments from strings to boolean values where necessary.
    use_local_mode = (str(use_local_mode).lower() == 'true')
    reuse_db = (str(reuse_db).lower() == 'true')
    run_selenium_tests = (str(run_selenium_tests).lower() == 'true')
    cmd_suffix = ''
    if reuse_db:
        cmd_suffix = " --keepdb"
    if tag and tag != "None":
        cmd_suffix += " --tag=%s" % tag
    if not run_selenium_tests:
        cmd_suffix += " --exclude-tag=selenium-test"
    elif tag and tag != "None":
        cmd_suffix += " --tag=selenium-test"

    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = project_dir + "lib/" + env + "/"
    src_dir = project_dir + "lib/" + env + "/src/temmpo/"

    with change_dir(src_dir):
        caller('%sbin/python3 manage.py test --noinput %s --tag=slow --settings=temmpo.settings.test_%s' % (venv_dir, cmd_suffix, db_type))

def recreate_db(env="test", database_name="temmpo_test", use_local_mode=False, project_dir=PROJECT_ROOT):
    """env="test",database_name="temmpo_test" # This method can only be used on an existing database based upon the way the credentials are looked up."""
    if database_name in ('temmpo_p', ):
        abort("Function should not be run against a production database.")

    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = project_dir + "lib/" + env + "/"

    with change_dir(venv_dir):
        caller('echo "DROP DATABASE %s; CREATE DATABASE %s;" | %sbin/python3 src/temmpo/manage.py dbshell --database=admin --settings=temmpo.settings.%s' % (database_name, database_name, venv_dir, env), pty=True)
        caller('echo "TeMMPo database was recreated".')


def add_missing_csv_headers_to_scores(project_dir=PROJECT_ROOT):
    """TMMA-262 - CSV files generated in the past do not have headers.

    NB: Needs to be run remotely against the demo and production VMs to ensure Bubble charts can be rendered.
    """
    results_directory = project_dir + "var/results/"
    file_header_info = [{'headers': 'Abstract IDs,', 'file_extension': '_abstracts.csv'},
                        {'headers': 'Mediators,Exposure counts,Outcome counts,Scores', 'file_extension': '_edge.csv'}, ]

    with cd(results_directory):
        for info in file_header_info:
            run('echo "%(headers)s" > headers%(file_extension)s' % info)
            csv_files = run('find . -name "*%(file_extension)s"' % info)
            for csv_file in csv_files.splitlines():
                if not files.contains(csv_file, info['headers'], exact=False):
                    run('cat "headers%s" "%s" > tmp-csv-file.txt && mv tmp-csv-file.txt "%s"' % (info['file_extension'], csv_file, csv_file))
            run("rm headers%(file_extension)s" % info)

def apply_csv_misquoting_fix(project_dir=PROJECT_ROOT):
    """To be run remotely only: TMMA-324 Bug fix edge files CSV misquoting"""
    affected_files = [
        "results_95__topresults_edge.csv",
        "results_113__topresults_edge.csv",
        "results_114__topresults_edge.csv",
        "results_123__topresults_edge.csv",
        "results_170__topresults_edge.csv",
        "results_173__topresults_edge.csv",
        "results_216__topresults_edge.csv",
        "results_316__topresults_edge.csv",
        "results_317__topresults_edge.csv",
        "results_318__topresults_edge.csv",
        "results_319__topresults_edge.csv",
        "results_320__topresults_edge.csv",
        "results_322__topresults_edge.csv",
        "results_324__topresults_edge.csv",
        "results_325__topresults_edge.csv",
        "results_336__topresults_edge.csv",
        "results_339__topresults_edge.csv",
        "results_344__topresults_edge.csv",
        "results_348__topresults_edge.csv",
        "results_351__topresults_edge.csv",
        "results_352__topresults_edge.csv",
        "results_353__topresults_edge.csv",
        "results_356__topresults_edge.csv",
        "results_428__topresults_edge.csv",
        "results_429__topresults_edge.csv",
        "results_430__topresults_edge.csv",
        ]

    replacement_pairs = {
        '"Anemia, Hemolytic", Autoimmune,': '"Anemia, Hemolytic, Autoimmune",',
        '"Antibodies, Monoclonal", Murine-Derived,': '"Antibodies, Monoclonal, Murine-Derived",',
        '"Antigens, Differentiation", T-Lymphocyte,': '"Antigens, Differentiation, T-Lymphocyte",',
        '"Arthroplasty, Replacement", Hip,': '"Arthroplasty, Replacement, Hip",',
        '"Arthroplasty, Replacement", Knee,': '"Arthroplasty, Replacement, Knee",',
        '"Carcinoma, Ductal", Breast,': '"Carcinoma, Ductal, Breast",',
        '"Contraceptives, Oral", Hormonal,': '"Contraceptives, Oral, Hormonal",',
        '"Death, Sudden", Cardiac,': '"Death, Sudden, Cardiac",',
        '"Receptors, Antigen, T-Cell", alpha-beta,': '"Receptors, Antigen, T-Cell, alpha-beta",',
        '"Receptors, Tumor Necrosis Factor", Member 25,': '"Receptors, Tumor Necrosis Factor, Member 25",',
        '"Receptors, Tumor Necrosis Factor", Type II,': '"Receptors, Tumor Necrosis Factor, Type II",',
        'Estrogens, Conjugated (USP),':'"Estrogens, Conjugated (USP)",',
        }
    # Allow function to be run locally or remotely
    results_directories = (project_dir + "var/results/v1", project_dir + "var/results")

    for results_directory in results_directories:
        with cd(results_directory):
            for affected_file in affected_files:
                if files.exists(affected_file):
                    print("About to replace text in %s/%s" % (results_directory, affected_file))
                    for find_str in replacement_pairs.keys():
                        run("sed -i -e 's/%s/%s/g\' %s" % (find_str, replacement_pairs[find_str], affected_file))

def pip_sync_requirements_file(env="dev", use_local_mode=True, project_dir=PROJECT_ROOT):
    use_local_mode = (str(use_local_mode).lower() == 'true')

    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = project_dir + "lib/" + env + "/"

    with change_dir(venv_dir+"src/temmpo/"):
        caller('../../bin/pip-compile --resolver=backtracking --generate-hashes --reuse-hashes --output-file requirements/requirements.txt requirements/requirements.in')
        caller('../../bin/pip-compile --resolver=backtracking --generate-hashes --reuse-hashes --output-file requirements/test.txt requirements/test.in')
        caller('../../bin/pip-compile --resolver=backtracking --generate-hashes --reuse-hashes --output-file requirements/dev.txt requirements/dev.in')

def pip_tools_update_requirements(env="dev", use_local_mode=True, package="", project_dir=PROJECT_ROOT):
    use_local_mode = (str(use_local_mode).lower() == 'true')
    if package:
        package = "--upgrade-package %s" % package

    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = project_dir + "lib/" + env + "/"

    with change_dir(venv_dir+"src/temmpo/"):
        caller('../../bin/pip-compile --resolver=backtracking --generate-hashes --reuse-hashes --upgrade %s --output-file requirements/requirements.txt requirements/requirements.in' % package)
        caller('../../bin/pip-compile --resolver=backtracking --generate-hashes --reuse-hashes --upgrade %s --output-file requirements/test.txt requirements/test.in' % package)
        caller('../../bin/pip-compile --resolver=backtracking --generate-hashes --reuse-hashes --upgrade %s --output-file requirements/dev.txt requirements/dev.in' % package)

def remove_incompleted_registrations(env="demo", use_local_mode=False, project_dir=PROJECT_ROOT):
    """env=demo,use_local_mode=False"""
    use_local_mode = (str(use_local_mode).lower() == 'true')
    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = project_dir + "lib/" + env + "/"
    src_dir = project_dir + "lib/" + env + "/src/temmpo/"

    with change_dir(src_dir):
        caller('%sbin/python3 manage.py remove_incompleted_registrations --settings=temmpo.settings.%s' % (venv_dir, env))

def force_reinstall_django_clamd_from_pypi(env="demo", use_local_mode=False, project_dir=PROJECT_ROOT):
    use_local_mode = (str(use_local_mode).lower() == 'true')
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = project_dir + "lib/" + env + "/"
    with change_dir(venv_dir+"src/temmpo/"):
        caller('../../bin/pip install --no-deps --force-reinstall django-clamd==1.0.0')
