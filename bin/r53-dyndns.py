#!/usr/bin/env python

"""
This will run as a dynamic dns agent and update a Route53 resource
record with your dynamic ip when the IP changes
"""

from optparse import OptionParser
from libr53dyndns.utils import daemonize , writePid , createLogDir , dropPrivs
from logging.handlers import RotatingFileHandler , StreamHandler
import libr53dyndns as r53
import os , logging , time

LOG = None

def getOpts():
    usage = '%prog [options]'
    p = OptionParser(usage=usage)
    p.add_option('-c' , '--config' , dest='config' , metavar='FILE' , 
        default='/etc/r53-dyndns.cfg' , help='Path to the config file '
        '[default: %default]')
    p.add_option('-d' , '--daemon' , action='store_true' , default=False ,
        dest='daemon' , help='Run as a daemon [default: %default]')
    p.add_option('-p' , '--pidfile' , metavar='FILE' , dest='pidfile' ,
        default='/var/run/r53-dyndns/r53-dyndns.pid' , help='The pidfile '
        'for the process.  Note that this will only be created when the '
        'process is being run as a daemon (-d option) [default: %default]')
    p.add_option('-D' , '--debug' , action='store_true' , default=False ,
        dest='debug' , help='Output debugging info [default: %default]')
    opts , args = p.parse_args()
    return (opts , args)

def getConfig(opts):
    conf = r53.DynConfig()
    conf.read((opts.config,))
    return conf

def setLogger(opts , conf):
    global LOG
    if LOG is None:
        return
    logger = logging.getLogger('r53-dyndns')
    handler = None
    if opts.daemon:
        handler = TimedRotatingFileHandler(opts.logfile , 'D' , 
            backupCount=conf.getint('main' , 'numlogs'))
    else:
        handler = StreamHandler()
    handler.setLevel(logging.INFO)
    if opts.debug:
        handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    LOG = logger
    return logger

def runContinuously(opts , conf):
    """
    This will just run in a loop every "update interval"
    """
    while True:
        try:
            run(opts , conf)
        except Exception as e:
            LOG.error('Error trying to check/update IPs: %s' % e)
        time.sleep(conf.getfloat('main' , 'updateInterval'))

def run(opts , conf):
    """
    This will initialize everything and run the check and update any
    records that need to be updated
    """
    ipGet = r53.IPGet(conf.get('main' , 'ipUrl') , 
        conf.getint('main' , 'iplookuptimeout') ,
        conf.getint('main' , 'iplookupmaxretries'))
    curIp = ipGet.getIP()
    LOG.debug('Current external IP: %s' % curIp)
    for fqdn in conf.getlist('main' , 'fqdns'):
        r53Obj = R53(fqdn , conf.get(fqdn , 'zone') ,
            conf.get(fqdn , 'accesskey') , conf.get(fqdn , 'secretkey') ,
            cont.getint(fqdn , 'ttl'))
        r53Ip = r53Obj.getIPR53()
        LOG.debug('Current IP for %s: %s' % (fqdn , r53Ip))
        if r53Ip != curIp:
            LOG.info('Changing IP for %s from %s to %s' % (fqdn , curIp , 
                r53Ip))
            r53Obj.update(curIp)

def main():
    opts , args = getOpts()
    conf = getConfig(opts)
    if opts.daemon:
        # Do the things we need to do when we daemonize
        try:
            createLogDir(os.path.dirname(conf.get('main' , 'logfile')))
        except Exception as e:
            print >> sys.stderr , 'Could not create log directory for ' \
                'logfile %s: %s' % (conf.get('main' , 'logfile') , e)
            sys.exit(1)
        setLogger(opts , conf)
        daemonize()
        try:
            writePid(opts.pidfile , conf.get('main' , 'runasuser') , 
                conf.get('main' , 'runasgroup'))
        except Exception as e:
            LOG.error('Could not write pidfile to %s' % opts.pidfile)
            sys.exit(1)
        try:
            dropPrivs(conf.get('main' , 'runasuser') , 
                conf.get('main' , 'runasgroup'))
        except Exception as e:
            LOG.error('Could not drop privileges to %s/%s: %s' % (
                conf.get('main' , 'runasuser') , 
                conf.get('main' , 'runasgroup') , e))
            sys.exit(1)
    setLogger(opts , conf)
    # Set the global log variable
    if opts.daemon:
        runContinuously(opts , conf)
    else:
        try:
            run(opts , conf)
        except Exception as e:
            LOG.error('Error trying to update IP: %s' % e)
            sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        msg = 'Unknown exception occurred: %s' % e
        if LOG is not None:
            LOG.error(msg)
        else:
            print >> sys.stderr , msg
        sys.exit(2)
