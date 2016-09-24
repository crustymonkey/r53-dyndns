#!/usr/bin/env python

"""
This will run as a dynamic dns agent and update a Route53 resource
record with your dynamic ip when the IP changes
"""

from optparse import OptionParser
from libr53dyndns.utils import daemonize, writePid, createLogDir, dropPrivs
from logging.handlers import TimedRotatingFileHandler
from ConfigParser import NoOptionError
import libr53dyndns as r53
import traceback
import os, logging, time, sys

__version__ = '0.1.1'

LOG = None

def getOpts():
    usage = '%prog [options]'
    p = OptionParser(usage=usage)
    p.add_option('-c', '--config', dest='config', metavar='FILE', 
        default='/etc/r53-dyndns.cfg', help='Path to the config file '
        '[default: %default]')
    p.add_option('-d', '--daemon', action='store_true', default=False,
        dest='daemon', help='Run as a daemon [default: %default]')
    p.add_option('-p', '--pidfile', metavar='FILE', dest='pidfile',
        default='/var/run/r53-dyndns/r53-dyndns.pid', help='The pidfile '
        'for the process.  Note that this will only be created when the '
        'process is being run as a daemon (-d option) [default: %default]')
    p.add_option('-l', '--log-to-file', action='store_true', default=False,
        dest='log_to_file', 
        help='Always log to the specified log file.  Normally, logs are '
        'written to the log file only when running as a daemon.  This will '
        'override the non-daemon behavior of logging to the terminal '
        '[default: %default]')
    p.add_option('-D', '--debug', action='store_true', default=False,
        dest='debug', help='Output debugging info [default: %default]')
    p.add_option('-V', '--version', action='store_true', default=False,
        dest='version', help='Print version and exit')
    opts, args = p.parse_args()
    if opts.version:
        print '%s: %s' % (os.path.basename(sys.argv[0]), __version__)
        sys.exit(0)
    return (opts, args)

def getConfig(opts):
    conf = r53.DynConfig()
    conf.read((opts.config,))
    return conf

def setLogger(opts, conf):
    global LOG
    if LOG is not None:
        return
    logger = logging.getLogger('r53-dyndns')
    handler = None
    if opts.daemon or opts.log_to_file:
        handler = TimedRotatingFileHandler(conf.get('main', 'logfile'), 'D', 
            backupCount=conf.getint('main', 'numlogs'))
    else:
        handler = logging.StreamHandler(sys.stderr)
    logger.setLevel(logging.INFO)
    if opts.debug:
        logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    LOG = logger
    return logger

def runContinuously(opts, conf):
    """
    This will just run in a loop every "update interval"
    """
    while True:
        try:
            run(opts, conf)
        except Exception as e:
            LOG.error('Error trying to check/update IPs: %s' % e)
        time.sleep(conf.getfloat('main', 'updateinterval'))

def run(opts, conf):
    """
    This will initialize everything and run the check and update any
    records that need to be updated
    """
    LOG.debug('Starting run')
    ipGet = r53.IPGet(conf.get('main', 'ipurl'), 
        conf.getint('main', 'iplookuptimeout'),
        conf.getint('main', 'iplookupmaxretries'))

    # If there's an old config, let's keep this as the previous versions,
    # which was v4 only
    try:
        updV4 = conf.getboolean('main', 'ipv4')
    except NoOptionError:
        updV4 = True
    try:
        updV6 = conf.getboolean('main', 'ipv6')
    except NoOptionError:
        updV6 = False

    curIpv4 = ipGet.getIP()
    curIpv6 = None
    if updV6:
        curIpv6 = ipGet.getIP(False)

    if curIpv4:
        LOG.debug('Current external IPv4: %s' % curIpv4)
    if curIpv6:
        LOG.debug('Current external IPv6: %s' % curIpv6)

    for fqdn in conf.getlist('main', 'fqdns'):
        r53Obj = r53.R53(fqdn, conf.get(fqdn, 'zone'),
            conf.get(fqdn, 'accesskey'), conf.get(fqdn, 'secretkey'),
            conf.getint(fqdn, 'ttl'))
        if updV4:
            r53Ip = r53Obj.get_ip_r53()
            LOG.debug('Current IPv4 for %s: %s' % (fqdn, r53Ip))
            if r53Ip != curIpv4:
                LOG.info('Changing IPv6 for %s from %s to %s' % (fqdn, r53Ip, 
                    curIpv4))
                r53Obj.update(curIpv4)
        if updV6:
            r53Ip = r53Obj.get_ip_r53(False)
            LOG.debug('Current IPv6 for %s: %s' % (fqdn, r53Ip))
            if r53Ip != curIpv6:
                LOG.info('Changing IPv6 for %s from %s to %s' % (fqdn, r53Ip,
                    curIpv6))
                r53Obj.update(ipv6=curIpv6)

def main():
    opts, args = getOpts()
    conf = getConfig(opts)
    if opts.daemon:
        # Do the things we need to do when we daemonize
        try:
            createLogDir(conf.get('main', 'logfile'), 
                conf.get('main', 'runasuser'), 
                conf.get('main', 'runasgroup'))
        except Exception as e:
            print >> sys.stderr, 'Could not create log directory for ' \
                'logfile %s: %s' % (conf.get('main', 'logfile'), e)
            sys.exit(1)
        setLogger(opts, conf)
        daemonize()
        try:
            writePid(opts.pidfile, conf.get('main', 'runasuser'), 
                conf.get('main', 'runasgroup'))
        except Exception as e:
            LOG.error('Could not write pidfile to %s' % opts.pidfile)
            sys.exit(1)
        if os.geteuid() == 0:
            try:
                dropPrivs(conf.get('main', 'runasuser'), 
                    conf.get('main', 'runasgroup'))
            except Exception as e:
                LOG.error('Could not drop privileges to %s/%s: %s' % (
                    conf.get('main', 'runasuser'), 
                    conf.get('main', 'runasgroup'), e))
                sys.exit(1)
    setLogger(opts, conf)
    # Set the global log variable
    if opts.daemon:
        runContinuously(opts, conf)
    else:
        try:
            run(opts, conf)
        except Exception as e:
            LOG.error('Error trying to update IP: %s' % e)
            if opts.debug:
                LOG.error(traceback.format_exc())
            sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        msg = 'Unknown exception occurred: %s' % e
        msg += traceback.format_exc()
        if LOG is not None:
            LOG.error(msg)
        else:
            print >> sys.stderr, msg
        sys.exit(2)
