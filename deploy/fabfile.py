import os

from fabric.api import *
from fabric.contrib import files

PROJECT_ROOT = "/usr/local/projects/temmpo/"
GIT_DIR = "/usr/local/projects/temmpo/lib/git/"
GIT_URL = 'git@bitbucket.org:researchit/temmpo.git'
PIP_VERSION = '9.0.1'
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


@hosts('localhost')
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
    with cd(GIT_DIR + egg):
        run('git pull')
        if action == 'merge':
            # make sure this is up to date branches before merging
            run('git checkout %s' % gfrom)
            run('git pull')
            run('git checkout %s' % gto)
            run('git pull')
            run('git merge -m "merge for release tagging" %s' % gfrom)
            run('git push')
        else:
            run('git checkout %s' % gfrom)
            run('git tag -a %s -m "%s"' % (gto, msg))
            run('git push origin %s' % gto)
        # Reset local git repo to master
        run('git checkout master')


def make_virtualenv(env="dev", configure_apache=False, clone_repo=False, branch=None, migrate_db=True, use_local_mode=False, requirements="base"):
    """NB: env = dev|prod"""
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
            caller('./bin/pip install -r src/temmpo/requirements/%s.txt' % requirements)

            # NB: TODO: Temmpo is not an installable egg, revify explicitly added to python path in WSGI file instead.

        # private_settings_sym_link = '%stemmpo/temmpo/private_settings.py' % src_dir
        # if not _is_link_local(private_settings_sym_link, use_local_mode):
        #     caller('ln -s %s.settings/private_settings.py %s' % (PROJECT_ROOT, private_settings_sym_link))

    # Set up logging
    if not _exists_local(PROJECT_ROOT + 'var/log/django.log', use_local_mode):
        caller('mkdir -p ' + PROJECT_ROOT + 'var/log/')
        caller('touch %svar/log/django.log' % PROJECT_ROOT)

    if migrate_db:
        with change_dir(PROJECT_ROOT + 'lib/' + env):
            caller('./bin/python src/temmpo/manage.py migrate --noinput --settings=temmpo.settings.%s' % env)

    if configure_apache:
        collect_static(env, use_local_mode)
        setup_apache(env, use_local_mode)


def deploy(host="localhost", env="dev", branch="master", tag=None, merge_from=None):
    """TODO: Needs testing NB: env = dev|prod.  Optionally tag and merge the release """

    if tag:
        taggit(gfrom="master", gto=tag, egg='temmpo')

    if merge_from:
        taggit(gfrom=merge_from, gto=branch, egg='temmpo')

    src_dir = PROJECT_ROOT + "lib/" + env + "/src/temmpo/"

    with settings(host_string=host, warn_only=True):
        with cd(src_dir):
            run('git fetch --all')
            run('git checkout %s' % branch)
            run('git pull')
            run('../../bin/python manage.py migrate --settings=temmpo.settings.%s')
            run('../../bin/python manage.py collectstatic --noinput --settings=temmpo.settings.%s')
            out = run('/usr/sbin/apache2ctl configtest', shell=False, pty=True)
            if out.find('Syntax OK') > -1:
                run('sudo /usr/sbin/apache2ctl restart')

    with cd("/tmp"):
        run('wget http://%s' % host)


def setup_apache(env="dev", use_local_mode=False):
    # Convert any string command line arguments to boolean values, where required.
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

    caller("sudo /sbin/apachectl configtest")
    caller("sudo /sbin/apachectl restart")
    caller("sudo /sbin/apachectl status")
    caller("wget 127.0.0.1")
    caller("rm index.html")
    with change_dir(venv_dir):
        caller("./bin/python src/temmpo/manage.py check --deploy --settings=temmpo.settings.%s" % env)


def collect_static(env="dev", use_local_mode=False):
    """Gather static files to be served by Apache"""

    # Convert any string command line arguments to boolean values, where required.
    use_local_mode = (str(use_local_mode).lower() == 'true')

    # Allow function to be run locally or remotely
    caller, change_dir = _toggle_local_remote(use_local_mode)
    venv_dir = PROJECT_ROOT + "lib/" + env

    with change_dir(venv_dir):
        caller('./bin/python src/temmpo/manage.py collectstatic --noinput --settings=temmpo.settings.%s' % env)
