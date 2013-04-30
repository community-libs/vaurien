import unittest
import requests
import time

from vaurienclient import Client
from vaurien.util import start_proxy, stop_proxy
from vaurien.tests.support import start_simplehttp_server


_PROXY = 'http://localhost:8000'


# we should provide a way to set an option
# for all behaviors at once
#
_OPTIONS = ['--behavior-delay-sleep', '1']


class TestHttpProxy(unittest.TestCase):
    def setUp(self):
        self._proxy_pid = start_proxy(options=_OPTIONS, log_level='error',
                                      log_output='/dev/null',
                                      protocol='http')
        self._web = start_simplehttp_server()
        time.sleep(.3)
        try:
            if self._web.poll():
                raise ValueError("Could not start the proxy")

            self.client = Client()

            assert self.client.get_behavior() == 'dummy'
        except Exception:
            self.tearDown()
            raise

    def tearDown(self):
        stop_proxy(self._proxy_pid)
        self._web.terminate()

    def test_proxy(self):
        # let's do a few simple request first to make sure the proxy works
        self.assertEqual(self.client.get_behavior(), 'dummy')
        times = []
        for i in range(10):
            start = time.time()
            try:
                res = requests.get(_PROXY)
            finally:
                times.append(time.time() - start)

            self.assertEqual(res.status_code, 200)

        fastest = min(times)

        # now let's try the various behaviors
        with self.client.with_behavior('blackout'):
            # oh look we broke it
            self.assertRaises(requests.ConnectionError, requests.get, _PROXY)
            self.assertEqual(self.client.get_behavior(), 'blackout')

        with self.client.with_behavior('delay'):
            # should work but be slower
            start = time.time()
            try:
                res = requests.get(_PROXY)
            finally:
                duration = time.time() - start

            self.assertEqual(res.status_code, 200)
            self.assertTrue(duration > fastest + 1)

        # we should be back to normal
        self.assertEqual(self.client.get_behavior(), 'dummy')
        res = requests.get(_PROXY)
        self.assertEqual(res.status_code, 200)
