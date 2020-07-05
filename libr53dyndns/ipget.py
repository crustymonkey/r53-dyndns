from dns.resolver import Resolver
from io import BytesIO
from libr53dyndns.errors import IPParseError, InvalidURL
from urllib.request import urlopen, Request
import re
import ssl
import time

class IPGet(object):
    """
    This defines a simple interface for grabbing the external IP address
    """
    # Define a simple ipv4 parser
    re_ipv4 = re.compile(r'(?:\d{1,3}\.){3}\d{1,3}')
    re_ipv6 = re.compile(r'(?:[a-f0-9:]+)')

    def __init__(self, url, timeout=3, retries=3):
        """
        Set up some instance variables

        url:str     The URL to use to get the external IP address
        timeout:int The timeout for each try in the IP retrieval
        retries:int The number of times to retry the connection
        """
        self.url = url
        self.timeout = int(timeout)
        self.max_retries = int(retries)
        self.resolver = Resolver()

    def get_ip(self, ipv4=True):
        """
        Returns a string representation of the external IPv4 address for
        this host

        ipv4:bool       If set to True, use IPv4 for the lookup.  If False,
                        use IPv6

        returns str     Returns the IP as a string
        """
        err = None
        tries = 0
        res = None
        while tries < self.max_retries:
            tries += 1
            try:
                res = self._get_url(ipv4)
            except Exception as e:
                err = e
                # Sleep for a second before a retry
                time.sleep(1)
            else:
                break

        if tries >= self.max_retries:
            # We have failed, raise the last error
            raise err

        # If we get here, we should have a result, parse the IP out of it
        m = self.re_ipv4.search(res) if ipv4 else self.re_ipv6.search(res)
        if not m:
            raise IPParseError('Could not parse an IPv4 address out of '
                'result from {}'.format(self.url))
        # We have parsed an IPv4 addr, return it
        return m.group(0)

    def _get_url(self, v4=True):
        ip_url, hostname = self._get_ip_url(v4)
        req = Request(ip_url, headers={'Host': hostname})
        resp = urlopen(req, context=self._get_no_verify_context())

        ip = resp.read()

        return ip.decode('utf-8').strip()

    def _get_ip_url(self, v4=True):
        m = re.match('(https?://)([^/]+)(.*)', self.url)
        if not m:
            raise InvalidURL('Could not parse url: {}'.format(self.url))

        port = ''
        if ':' in m.group(2):
            hostname, port = m.group(2).split(':')
        else:
            hostname = m.group(2)
        
        # Get the ip for this hostname
        qtype = 'A' if v4 else 'AAAA'
        ip = self._query(hostname, qtype)
        ip = ip if v4 else '[{}]'.format(ip)
        
        ip_url = '{}{}{}{}'.format(
            m.group(1),
            ip,
            ':{}'.format(port) if port else '',
            m.group(3),
        )

        return (ip_url, hostname)

    def _get_no_verify_context(self):
        """
        Turn off certificate validation for the ip lookups.  This allows
        for using IPs in the URL with an explicit Host header and bypasses
        the need for pycurl
        """
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        return ctx

    def _query(self, hostname, qtype, single=True):
        resp = self.resolver.query(hostname, qtype)
        if single:
            return str(resp[0])

        return [str(a) for a in resp]
