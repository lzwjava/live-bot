import os

from fabric.api import run, sudo, env, cd, local, prefix, put, lcd, settings
from fabric.contrib.project import rsync_project
from fabric.contrib.files import exists, sed
from fabric.utils import puts

server_dir = '/root/wxBot'
tmp_dir = '/tmp/wxBot' + str(os.getpid())


def _set_user_dir():
    global server_dir
    with settings(warn_only=True):
        issue = run('id root').lower()


def _prepare_local_website():
    local('mkdir -p %s' % tmp_dir)
    local('cp *.py *.jpg %s' % tmp_dir)


def prepare_remote_dirs():
    _set_user_dir()
    if not exists(server_dir):
        sudo('mkdir -p %s' % server_dir)
        sudo('chmod -R 755 %s' % server_dir)
        sudo('chown %s %s' % ('root', server_dir))


def _clean_local_dir():
    local('rm -r %s' % tmp_dir)


def host_type():
    run('uname -s')


def deploy():
    _prepare_local_website()
    prepare_remote_dirs()
    rsync_project(local_dir=tmp_dir + '/', remote_dir=server_dir, delete=True)
    _clean_local_dir()
