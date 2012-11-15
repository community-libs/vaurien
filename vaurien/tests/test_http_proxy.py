import unittest
import requests
import sys
import time

from vaurien.client import Client
from vaurien.util import start_proxy, stop_proxy
from vaurien.tests.util import start_web_server


_PROXY = 'http://localhost:8000'
_SERVER = [sys.executable, '-m', 'SimpleHTTPServer', '8888']


# we should provide a way to set an option
# for all handlers at once
#
_OPTIONS = ['--handler-delay-protocol', 'http',
            '--handler-delay-sleep', '1',
            '--handler-dummy-protocol', 'http',
            ]


class TestHttpProxy(unittest.TestCase):
    def setUp(self):
        self._proxy_pid = start_proxy(options=_OPTIONS, log_level='error',
                                      log_output='/dev/null')
        self._web = start_web_server()
        time.sleep(.5)
        try:
            if self._web.poll():
                raise ValueError("Could not start the proxy")

            self.client = Client()

            assert self.client.get_handler() == 'dummy'
        except Exception:
            self.tearDown()
            raise

    def tearDown(self):
        stop_proxy(self._proxy_pid)
        self._web.terminate()

    def test_proxy(self):
        # let's do a few simple request first to make sure the proxy works
        self.assertEqual(self.client.get_handler(), 'dummy')
        times = []

        for i in range(10):
            start = time.time()
            try:
                res = requests.get(_PROXY)
            finally:
                times.append(time.time() - start)

            self.assertEqual(res.status_code, 200)

        fastest = min(times)

        # now let's try the various handlers
        with self.client.with_handler('blackout'):
            # oh look we broke it
            self.assertRaises(requests.ConnectionError, requests.get, _PROXY)
            self.assertEqual(self.client.get_handler(), 'blackout')

        with self.client.with_handler('delay'):
            # should work but be slower
            start = time.time()
            try:
                res = requests.get(_PROXY)
            finally:
                duration = time.time() - start

            self.assertEqual(res.status_code, 200)
            self.assertTrue(duration > fastest + 1)

        # we should be back to normal
        self.assertEqual(self.client.get_handler(), 'dummy')
        res = requests.get(_PROXY)
        self.assertEqual(res.status_code, 200)
