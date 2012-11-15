import unittest
import requests
import time
from StringIO import StringIO

from vaurien.client import Client
from vaurien.util import start_proxy, stop_proxy
from vaurien.tests.util import start_web_server


_PROXY = 'http://localhost:8000'
_REQCONFIG = {'verbose': StringIO()}


class TestSimpleProxy(unittest.TestCase):
    def setUp(self):
        self._proxy_pid = start_proxy(log_output='/dev/null',
                                      log_level='error')
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

    def test_existing_handlers(self):
        wanted = ['blackout', 'delay', 'dummy', 'error', 'hang']
        self.assertEqual(self.client.list_handlers(), wanted)

    def test_proxy(self):
        # let's do a few simple request first to make sure the proxy works
        self.assertEqual(self.client.get_handler(), 'dummy')
        for i in range(10):
            res = requests.get(_PROXY, config=_REQCONFIG)
            self.assertEqual(res.status_code, 200)

        # now let's add a bit of havoc
        with self.client.with_handler('blackout'):
            # oh look we broke it
            self.assertRaises(requests.ConnectionError, requests.get, _PROXY,
                              config=_REQCONFIG)
            self.assertEqual(self.client.get_handler(), 'blackout')

        # we should be back to normal
        self.assertEqual(self.client.get_handler(), 'dummy')
        res = requests.get(_PROXY, config=_REQCONFIG)
        self.assertEqual(res.status_code, 200)
