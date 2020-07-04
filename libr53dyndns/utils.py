
"""
Define some utility functions
"""

import os , sys , pwd , grp

def get_uid_gid(user , group):
    """
    Convenience function to get the corresponding uid/gid for 
    username/groupname
    """
    uid = pwd.getpwnam(user).pw_uid
    gid = grp.getgrnam(group).gr_gid
    return (uid , gid)


def drop_privs(user , group):
    uid , gid = get_uid_gid(user , group)
    os.setregid(gid , gid)
    os.setreuid(uid , uid)


def create_log_dir(logfile , owner , group):
    logdir = os.path.dirname(logfile)
    uid , gid = get_uid_gid(owner , group)
    if not os.path.isdir(logdir):
        os.makedirs(logdir , 0o755)
        os.chown(logdir , uid , gid)
    if not os.path.isfile(logfile):
        # Just create the file
        open(logfile , 'w').close()
    os.chown(logfile , uid , gid)
    os.chmod(logfile , 0o644)


def daemonize(stdin='/dev/null' , stdout='/dev/null' , stderr='/dev/null'):
    if os.fork() > 0:
        sys.exit(0)
    os.chdir('/')
    os.umask(0)
    os.setsid()
    if os.fork() > 0:
        sys.exit(0)

    for f in (sys.stdout , sys.stderr):
        f.flush()

    si = open(stdin , 'r')
    so = open(stdout , 'a+')
    se = open(stderr , 'a+')
    os.dup2(si.fileno() , sys.stdin.fileno())
    os.dup2(so.fileno() , sys.stdout.fileno())
    os.dup2(se.fileno() , sys.stderr.fileno())


def write_pid(pidFile , owner , group):
    pidDir = os.path.dirname(pidFile)
    uid , gid = get_uid_gid(owner , group)

    if not os.path.isdir(pidDir):
        os.makedirs(pidDir , 0o755)
        os.chown(pidDir , uid , gid)

    pid = os.getpid()
    with open(pidFile , 'w') as fh:
        fh.write(str(pid))

    os.chown(pidFile , uid , gid)
    os.chmod(pidFile , 0o644)
