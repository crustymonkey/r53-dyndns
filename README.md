# r53-dyndns #

## Overview ##

This is a dynamic DNS agent which uses Amazon's Route53 and your own 
domain as the dns fqdn to update.

**BACKWARDS COMPATIBLE BREAKAGE: Due to a dependency change from `pycurl` to
`dnspython` in 0.4.0, be careful with a 0.4.0 upgrade!**

## Requirements ##
* python3 boto3 version >= 1.3.0.  Just head over to the github page and
  download the latest from the develop branch. Note that (at the time of
  this writing), the version included in your package manager is likely
  too old.  https://github.com/boto/boto3
* python3 dnspython version >= 1.16.0.  You can get it from github at 
  https://github.com/rthalley/dnspython or install via your package manager 
  or pip.
* An AWS Account (or at least an IAM user with access to the zone(s) you
  wish to update).  This should be fairly obvious...

## Install ##
* You can download this from github: https://github.com/crustymonkey/r53-dyndns
* You can install with **pip** (or easy_install): pip install r53-dyndns

### Download ###
    $ wget -O r53-dyndns-master.zip 'https://github.com/crustymonkey/r53-dyndns/archive/master.zip'
    $ unzip r53-dyndns-master.zip
    $ cd r53-dyndns-master
    $ sudo python setup.py install

## Usage ##
### Config ###
Your config file (r53-dyndns.cfg) should be installed in /etc (if it's not
there, it's likely in /usr/local/etc).  Open that up, read through the 
comments and set up everything as you desire.

### Running ###
There are basically 2 ways you can run this: a cron job or as a daemon.  I
am going to assume a basic familiarity with your choice of method.

#### Running a Cron Job (the easy method) ####
Once you have your config file setup, all you have to do is set up a cron job
which runs the script every minute.  Provided your config file is in the
default location (/etc/r53-dyndns.cfg) and the script is installed in 
/usr/bin, you can just add the following to your crontab:

    * * * * *       /usr/bin/r53-dyndns.py

#### Running a Daemon (advanced method) ####
I ***highly recommend*** you configure a proper run as user/group in the config
and start this as root.  This will then set up the log and run directories
with the proper permissions.

This is really not all that difficult or advanced, but since I'm not including
init scripts in this package, it means a bit of work on your part to make
this run on startup.  If your config file is setup and all the files are in
the expected locations, you should be able to just run the script with the
**-d** option:

    /usr/bin/r53-dyndns.py -d
