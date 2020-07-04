
from libr53dyndns.errors import IPParseError
from io import BytesIO
import pycurl
import re, time

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
                'result from %s' % self.url)
        # We have parsed an IPv4 addr, return it
        return m.group(0)

    def _get_url(self, v4=True):
        c = pycurl.Curl()
        buf = BytesIO()

        c.setopt(c.URL, self.url)
        c.setopt(c.WRITEDATA, buf)
        c.setopt(c.CONNECTTIMEOUT, self.timeout)
        ipresolve = c.IPRESOLVE_V4 if v4 else c.IPRESOLVE_V6
        c.setopt(c.IPRESOLVE, ipresolve)
        c.perform()
        c.close()

        ret = buf.getvalue()
        buf.close()

        return ret.decode('utf-8')
