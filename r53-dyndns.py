#!/usr/bin/env python3

"""
This will run as a dynamic dns agent and update a Route53 resource
record with your dynamic ip when the IP changes
"""

from argparse import ArgumentParser
from libr53dyndns.utils import daemonize, write_pid, create_log_dir, drop_privs
from logging.handlers import TimedRotatingFileHandler
from configparser import NoOptionError
import libr53dyndns as r53
import traceback
import os, logging, time, sys

__version__ = r53.__version__

LOG = None

def get_args():
    p = ArgumentParser()
    p.add_argument('-c', '--config', dest='config', metavar='FILE', 
        default='/etc/r53-dyndns.cfg', help='Path to the config file '
        '[default: %(default)s]')
    p.add_argument('-d', '--daemon', action='store_true', default=False,
        dest='daemon', help='Run as a daemon [default: %(default)s]')
    p.add_argument('-p', '--pidfile', metavar='FILE', dest='pidfile',
        default='/var/run/r53-dyndns/r53-dyndns.pid', help='The pidfile '
        'for the process.  Note that this will only be created when the '
        'process is being run as a daemon (-d option) [default: %(default)s]')
    p.add_argument('-l', '--log-to-file', action='store_true', default=False,
        dest='log_to_file', 
        help='Always log to the specified log file.  Normally, logs are '
        'written to the log file only when running as a daemon.  This will '
        'override the non-daemon behavior of logging to the terminal '
        '[default: %(default)s]')
    p.add_argument('-D', '--debug', action='store_true', default=False,
        dest='debug', help='Output debugging info [default: %(default)s]')
    p.add_argument('-V', '--version', action='store_true', default=False,
        dest='version', help='Print version and exit')

    args = p.parse_args()
    if args.version:
        print('{}: {}'.format(os.path.basename(sys.argv[0]), __version__))
        sys.exit(0)

    return args


def get_config(args):
    conf = r53.DynConfig()
    conf.read((args.config,))
    return conf

def set_logger(args, conf):
    global LOG
    if LOG is not None:
        return
    logger = logging.getLogger('r53-dyndns')
    handler = None
    if args.daemon or args.log_to_file:
        handler = TimedRotatingFileHandler(conf.get('main', 'logfile'), 'D', 
            backupCount=conf.getint('main', 'numlogs'))
    else:
        handler = logging.StreamHandler(sys.stderr)
    logger.setLevel(logging.INFO)
    if args.debug:
        logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    LOG = logger
    return logger

def run_continuously(args, conf):
    """
    This will just run in a loop every "update interval"
    """
    while True:
        try:
            run(args, conf)
        except Exception as e:
            LOG.error('Error trying to check/update IPs: {}'.format(e))
        time.sleep(conf.getfloat('main', 'updateinterval'))

def run(args, conf):
    """
    This will initialize everything and run the check and update any
    records that need to be updated
    """
    LOG.debug('Starting run')
    ip_get = r53.IPGet(
        conf.get('main', 'ipurl'), 
        conf.getint('main', 'iplookuptimeout'),
        conf.getint('main', 'iplookupmaxretries'),
    )

    # If there's an old config, let's keep this as the previous versions,
    # which was v4 only
    try:
        upd_v4 = conf.getboolean('main', 'ipv4')
    except NoOptionError:
        upd_v4 = True
    try:
        upd_v6 = conf.getboolean('main', 'ipv6')
    except NoOptionError:
        upd_v6 = False

    cur_ipv4 = ip_get.get_ip()
    cur_ipv6 = None
    if upd_v6:
        try:
            cur_ipv6 = ip_get.get_ip(False)
        except Exception as e:
            LOG.warning('Could not get an IPv6 address')

    if cur_ipv4:
        LOG.debug('Current external IPv4: {}'.format(cur_ipv4))
    if cur_ipv6:
        LOG.debug('Current external IPv6: {}'.format(cur_ipv6))

    for fqdn in conf.getlist('main', 'fqdns'):
        r53_obj = r53.R53(fqdn, conf.get(fqdn, 'zone'),
            conf.get(fqdn, 'accesskey'), conf.get(fqdn, 'secretkey'),
            conf.getint(fqdn, 'ttl'))

        if cur_ipv4 and upd_v4:
            r53_ip = r53_obj.get_ip_r53()
            LOG.debug('Current IPv4 for {}: {}'.format(fqdn, r53_ip))
            if r53_ip != cur_ipv4:
                LOG.info('Changing IPv4 for {} from {} to {}'.format(
                    fqdn, r53_ip, cur_ipv4))
                r53_obj.update(cur_ipv4)

        if cur_ipv6 and upd_v6:
            r53_ip = r53_obj.get_ip_r53(False)
            LOG.debug('Current IPv6 for {}: {}'.format(fqdn, r53_ip))
            if r53_ip != cur_ipv6:
                LOG.info('Changing IPv6 for {} from {} to {}'.format(
                    fqdn, r53_ip, cur_ipv6))
                r53_obj.update(ipv6=cur_ipv6)

def main():
    args = get_args()
    conf = get_config(args)
    if args.daemon:
        # Do the things we need to do when we daemonize
        try:
            create_log_dir(
                conf.get('main', 'logfile'), 
                conf.get('main', 'runasuser'), 
                conf.get('main', 'runasgroup'),
            )
        except Exception as e:
            print('Could not create log directory for logfile {}: {}'.format(
                conf.get('main', 'logfile'), e), 
                file=sys.stderr,
            )
            sys.exit(1)

        set_logger(args, conf)
        daemonize()

        try:
            write_pid(
                args.pidfile,
                conf.get('main', 'runasuser'),
                conf.get('main', 'runasgroup'),
            )
        except Exception as e:
            LOG.error('Could not write pidfile to {}'.format(args.pidfile))
            sys.exit(1)

        if os.geteuid() == 0:
            try:
                drop_privs(conf.get('main', 'runasuser'), 
                    conf.get('main', 'runasgroup'))
            except Exception as e:
                LOG.error('Could not drop privileges to {}/{}: {}'.format(
                    conf.get('main', 'runasuser'), 
                    conf.get('main', 'runasgroup'),
                    e,
                ))
                sys.exit(1)

    set_logger(args, conf)
    # Set the global log variable
    if args.daemon:
        run_continuously(args, conf)
    else:
        try:
            run(args, conf)
        except Exception as e:
            LOG.error('Error trying to update IP: {}'.format(e))
            if args.debug:
                LOG.error(traceback.format_exc())
            sys.exit(1)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        msg = 'Unknown exception occurred: {}'.format(e)
        msg += traceback.format_exc()
        if LOG is not None:
            LOG.error(msg)
        else:
            print(msg, file=sys.stderr)
        sys.exit(2)
