from fabric.api import *

PROJECT_LIB = "/usr/local/projects/tmma"
GIT_DIR = "/usr/local/projects/tmma/lib/git/"


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
        print '(You can delete a tag and add a new one with the same name - but its bad karma)'
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


def deploy(host="tmma-dev.ilrt.bris.ac.uk", env="dev", branch="demo_stable", tag=None, merge_from='master'):
    """Optionally tag the release"""

    if tag:
        taggit(gfrom="master", gto=tag, egg='temmpo')

    if merge_from:
        taggit(gfrom=merge_from, gto=branch, egg='temmpo')

    src_dir = PROJECT_LIB + "/lib/" + env + "/src/temmpo/"

    with settings(host_string=host, warn_only=True):
        with cd(src_dir):
            run('git fetch --all')
            run('git checkout %s' % branch)
            run('git pull')
            run('../../bin/python manage.py migrate')
            run('../../bin/python manage.py collectstatic --noinput')
            out = run('/usr/sbin/apache2ctl configtest', shell=False, pty=True)
            if out.find('Syntax OK') > -1:
                run('sudo /usr/sbin/apache2ctl restart')

    with cd("/tmp"):
        run('wget http://%s' % host)
