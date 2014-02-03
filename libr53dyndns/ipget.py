
from libr53dyndns.errors import IPParseError
import urllib2 , re , time

class IPGet(object):
    """
    This defines a simple interface for grabbing the external IP address
    """
    # Define a simple ipv4 parser
    reIpv4 = re.compile(r'(?:\d{1,3}\.){3}\d{1,3}')

    def __init__(self , url , timeout=3 , retries=3):
        """
        Set up some instance variables

        url:str     The URL to use to get the external IP address
        timeout:int The timeout for each try in the IP retrieval
        retries:int The number of times to retry the connection
        """
        self.url = url
        self.timeout = int(timeout)
        self.maxRetries = int(retries)
        self._opener = self._getOpener()

    def getIP(self):
        """
        Returns a string representation of the external IPv4 address for
        this host
        """
        err = None
        tries = 0
        res = None
        while tries < self.maxRetries:
            tries += 1
            try:
                res = self._opener.open(self.url , timeout=self.timeout)
            except Exception as e:
                err = e
                # Sleep for a second before a retry
                time.sleep(1)
            else:
                break
        if tries >= self.maxRetries:
            # We have failed, raise the last error
            raise err
        # If we get here, we should have a result, parse the IP out of it
        m = self.reIpv4.search(res.read())
        if not m:
            raise IPParseError('Could not parse an IPv4 address out of '
                'result from %s' % self.url)
        # We have parsed an IPv4 addr, return it
        return m.group(0)

    def _getOpener(self):
        """
        We aren't adding any odd handlers now, but if there was a need
        in the future, the opener generation encapsulated here
        """
        opener = urllib2.build_opener()
        return opener
