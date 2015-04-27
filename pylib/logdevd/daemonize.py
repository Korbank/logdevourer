#!/usr/bin/python
'''
Daemonization helpers
---------------------

.. autoclass:: PidFile
   :members:

'''
#-----------------------------------------------------------------------------

import os
import sys
import pwd
import grp

#-----------------------------------------------------------------------------

PARENT = 1
CHILD = 2

#-----------------------------------------------------------------------------
# PidFile(filename) {{{

class PidFile:
    '''
    Handle for pid file. The file will be deleted when the instance is
    destroyed, if the file ownership was claimed (see :meth:`claim`).
    '''

    def __init__(self, filename):
        '''
        :param filename: name of the pid file
        :type filename: string
        '''
        if filename is not None:
            self.filename = os.path.abspath(filename)
            self.fd = open(self.filename, 'w', 0) # TODO: atomic create-or-fail
        else:
            self.filename = None
            self.fd = None
        self.pid = None
        self.remove_on_close = False
        self.update()

    def claim(self):
        '''
        Claim the ownership of the pid file. Owner process is responsible for
        removing it at the end.
        '''
        self.remove_on_close = True

    def update(self):
        '''
        Update content of pid file with current process' PID.
        '''
        if self.fd is None:
            return
        self.pid = os.getpid()
        self.fd.seek(0)
        self.fd.write("%d\n" % (self.pid))
        self.fd.truncate()

    def close(self):
        '''
        Close pid file *without* removing it.
        '''
        if self.fd is not None:
            return
        self.fd.close()
        self.fd = None

    def __del__(self):
        if self.fd is None:
            # do nothing if closed already
            return

        self.fd.close()
        if self.remove_on_close and self.pid == os.getpid():
            # only remove the file if owner
            os.unlink(self.filename)

# }}}
#-----------------------------------------------------------------------------
# setguid(user, group) {{{

def setguid(user, group):
    '''
    :param user: username to change UID to
    :param group: group name to change GID to

    Set UID and GID of current process.
    '''
    uid = None
    gid = None

    if user is not None:
        pw_user = pwd.getpwnam(user)
        uid = pw_user.pw_uid
        gid = pw_user.pw_gid # will be replaced if group was specified

    if group is not None:
        gr_group = grp.getgrnam(group)
        gid = gr_group.gr_gid

    # after UID change it may be impossible to change primary group
    if gid is not None:
        os.setgid(gid)
    if uid is not None:
        os.setuid(uid)

# }}}
#-----------------------------------------------------------------------------
# detach(new_cwd) {{{

def detach(new_cwd = None):
    '''
    :param new_cwd: directory to :func:`chdir` to (``None`` if no change
      needed)

    Detach current program from terminal (:func:`fork` + :func:`exit`).

    Detached (child) process will have *STDIN*, *STDOUT* and *STDERR*
    redirected to :file:`/dev/null`.
    '''
    if os.fork() == 0:
        if new_cwd is not None:
            os.chdir(new_cwd)
        child_process()
        return CHILD
    else:
        parent_process()
        return PARENT

def child_process():
    '''
    Operations to initialize child process after detaching.

    This consists mainly of redirecting *STDIN*, *STDOUT* and *STDERR* to
    :file:`/dev/null`.

    **NOTE**: This is not the place to acknowledge success. There are other
    operations, like creating listening sockets. See :func:`detach_succeeded`.
    '''
    # replace STDIN, STDOUT and STDERR
    sys.stdin = open('/dev/null')
    sys.stdout = sys.stderr = open('/dev/null', 'w')

def parent_process():
    '''
    Operations to do in parent process, excluding terminating the parent.
    '''
    # TODO: wait for child to acknowledge success
    pass

# }}}
#-----------------------------------------------------------------------------

#-----------------------------------------------------------------------------
# vim:ft=python:foldmethod=marker
