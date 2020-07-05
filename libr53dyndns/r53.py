
import boto3
import time
import socket
import re

from libr53dyndns.errors import InvalidInputError

class R53(object):
    """
    Wrap the boto Route53 interface with some specific convenience
    operations
    """
    
    def __init__(self, fqdn, zone, ak, sk, ttl=60):
        """
        Initialize everything given the inputs

        domain:str      The fqdn of the resource record we will be updating
        zone:str        The name of the zone.  This should be root name
                        of the fqdn
        ak:str          The access key for the Route53 connection
        sk:str          The secret key for the Route53 connection
        ttl:int         The ttl (in seconds) to use for updates.  This 
                        should be something low, like 60 seconds
        """
        self.bogus_v4 = '169.254.0.1'
        self.bogus_v6 = 'fe80::1'
        self.fqdn = fqdn.lower()
        self.zone = zone.lower()
        self.ttl = int(ttl)
        self._r53 = boto3.client('route53', aws_access_key_id=ak, 
            aws_secret_access_key=sk)
        self._zone_id = None

    def get_ip_r53(self, v4=True):
        """
        Returns the IP currently defined in your Route53 rrset for 
        your fqdn
        """
        rec = self._get_record_ip(v4)
        if rec is None:
            # If we don't have a record for this, we will automatically
            # create it with a bogus entry and return
            if v4:
                self.update(ipv4=self.bogus_v4)
                return self.bogus_v4
            else:
                self.update(ipv6=self.bogus_v6)
                return self.bogus_v6
        return rec

    def get_ip_dns(self, v4=True):
        """
        This just does a dns lookup to return the IP for the fqdn.  This
        should be faster than hitting the R53 API.  Note that this
        is not necessarily authoritative in terms of what's actually
        in R53 due to TTLs
        """
        addrs = socket.getaddrinfo(self.fqdn, 80, 0, 0, socket.IPPROTO_TCP)
        for addr in addrs:
            if v4 and addr[0] == socket.AF_INET:
                return addr[4][0]
            elif not v4 and addr[0] == socket.AF_INET6:
                return addr[4][0]

    def update(self, ipv4=None, ipv6=None):
        """
        Update the fqdn with the new IP addr
        """
        if ipv4 is None and ipv6 is None:
            raise InvalidInputError('You must specify either (or both) an '
                'ipv4 address or ipv6 address to update')
        changes = []
        if ipv4:
            chg = self._get_chg_frame()
            chg['ResourceRecordSet']['ResourceRecords'].append({'Value': ipv4})
            changes.append(chg)
        if ipv6:
            chg = self._get_chg_frame()
            chg['ResourceRecordSet']['Type'] = 'AAAA'
            chg['ResourceRecordSet']['ResourceRecords'].append({'Value': ipv6})
            changes.append(chg)

        resp = self._r53.change_resource_record_sets(
            HostedZoneId=self._get_zone_id(),
            ChangeBatch={
                'Comment': 'Updated at {0}'.format(time.ctime()),
                'Changes': changes,
            },
        )

        return resp

    def _get_record_ip(self, v4=True):
        """
        Gets the Record object for the fqdn
        """
        rtype = 'A' if v4 else 'AAAA'
        resp = self._r53.list_resource_record_sets(
            HostedZoneId=self._get_zone_id(),
            StartRecordName=self.fqdn,
            StartRecordType=rtype,
            MaxItems='1',
        )

        dns_name = resp['ResourceRecordSets'][0]['Name'].rstrip('.') 

        if self._pretty_dns_name(dns_name) == self.fqdn and \
                resp['ResourceRecordSets'][0]['Type'] == rtype:
            return resp['ResourceRecordSets'][0]['ResourceRecords'][0]['Value']

        return None

    def _get_zone_id(self):
        """
        Retrieve the appropriate zone
        """
        if self._zone_id is not None:
            return self._zone_id

        zones = self._r53.list_hosted_zones_by_name(DNSName=self.zone)
        for zone in zones['HostedZones']:
            # The first zone should be the one we are looking for, but we
            # won't make assumptions
            if zone['Name'].rstrip('.') == self.zone:
                self._zone_id = zone['Id']
                return self._zone_id

        # If we get here, the zone isn't found, raise an exception
        raise ZoneNotFoundError('Could not find the zone: {0}'.format(
            self.zone))
    
    def _get_chg_frame(self):
        """
        This gets a baseline setup change batch
        """
        chg_framework = {
            'Action': 'UPSERT',
            'ResourceRecordSet': {
                'Name': self.fqdn,
                'Type': 'A',
                'TTL': self.ttl,
                'ResourceRecords': [],
            },
        }

        return chg_framework

    def _octal_replace(self, x):
        """
        This fixes problems with wildcard dns
        Based on the gist below
        https://gist.github.com/meonkeys/4482362#file-route53octals-py-L13
        """
        c = int(x.group(1), 8)
        if c > 0x20 and c < 0x2e or c > 0x2e and c < 0x7f:
            return chr(c)
        else:
            return x.group(0)

    def _pretty_dns_name(self, value):
        """
        R53.prettyDnsName handles encoded R53 API response with 
        *,- etc included
        """
        return re.sub(r'\\(\d{3})', self._octal_replace, value)
