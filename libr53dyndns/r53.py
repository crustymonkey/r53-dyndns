
from boto.route53.connection import Route53Connection
import boto3
import socket

class R53(object):
    """
    Wrap the boto Route53 interface with some specific convenience
    operations
    """

    def __init__(self, fqdn , zone , ak , sk , ttl=60):
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
        self.bogusIp = '169.254.0.1'
        self.fqdn = fqdn.lower()
        self.zone = zone.lower()
        self.ttl = int(ttl)
        self._r53 = boto3.client('route53', aws_access_key_id=ak, 
            aws_secret_access_key=sk)
        self._r53Zone = None

    def getIPR53(self, v4=True):
        """
        Returns the IP currently defined in your Route53 rrset for 
        your fqdn
        """
        rec = self._getRecord()
        if rec is None:
            # If we don't have a record for this, we will automatically
            # create it with a bogus entry and return
            self.create(self.bogusIp)
            return self.bogusIp
        return rec.to_print()

    def getIPDNS(self, v4=True):
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

    def update(self, ip, v4=True):
        """
        Update the fqdn with the new IP address
        """
        if self._r53Zone is None:
            self._r53Zone = self._r53.get_zone(self.zone)
        self._r53Zone.update_a(self.fqdn, ip , self.ttl)

    def create(self, ip, v4=True):
        """
        Create an A record with fqdn and the passed IP address
        """
        if self._r53Zone is None:
            self._r53Zone = self._r53.get_zone(self.zone)
        self._r53Zone.add_a(self.fqdn, ip , self.ttl)

    def _getRecord(self):
        """
        Gets the Record object for the fqdn
        """
        if self._r53Zone is None:
            self._r53Zone = self._r53.get_zone(self.zone)
        return self._r53Zone.get_a(self.fqdn)
