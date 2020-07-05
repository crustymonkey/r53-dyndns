from libr53dyndns.ipget import IPGet
from unittest.mock import MagicMock, patch
import unittest

class TestIPGet(unittest.TestCase):

    def test_get_ip_url(self):
        ip_val = '1.2.3.4'
        hostname = 'a.b.c.d'
        mock = MagicMock(return_value=ip_val)
        test_urls = self._get_test_urls(hostname, ip_val)

        # test v4 first
        with patch.object(IPGet, '_query', mock):
            for url, resp_url in test_urls:
                ipg = IPGet(url)
                ip_url, resp_host = ipg._get_ip_url()

                self.assertEqual(ip_url, resp_url)
                self.assertEqual(hostname, resp_host)

        # now test v6
        ip_val = '2002::1'
        mock = MagicMock(return_value=ip_val)
        test_urls = self._get_test_urls(hostname, ip_val)

        with patch.object(IPGet, '_query', mock):
            for url, resp_url in test_urls:
                ipg = IPGet(url)
                ip_url, resp_host = ipg._get_ip_url(False)

                self.assertEqual(ip_url, resp_url)
                self.assertEqual(hostname, resp_host)

    def _get_test_urls(self, hostname, ip_val):
        if ':' in ip_val:
            ip_val = '[{}]'.format(ip_val)

        test_urls = (
            (
                'http://{}'.format(hostname),
                'http://{}'.format(ip_val),
            ),
            (
                'https://{}'.format(hostname),
                'https://{}'.format(ip_val),
            ),
            (
                'http://{}:81'.format(hostname),
                'http://{}:81'.format(ip_val),
            ),
            (
                'https://{}:81'.format(hostname),
                'https://{}:81'.format(ip_val),
            ),
            (
                'http://{}/monkey'.format(hostname),
                'http://{}/monkey'.format(ip_val),
            ),
            (
                'https://{}/monkey'.format(hostname),
                'https://{}/monkey'.format(ip_val),
            ),
            (
                'http://{}:81/monkey'.format(hostname),
                'http://{}:81/monkey'.format(ip_val),
            ),
            (
                'https://{}:81/monkey'.format(hostname),
                'https://{}:81/monkey'.format(ip_val),
            ),
        )

        return test_urls
