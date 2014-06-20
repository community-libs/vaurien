import unittest
import requests
import time

from vaurienclient import Client
from vaurien.util import start_proxy, stop_proxy
from vaurien.tests.support import start_simplehttp_server


_PROXY = 'http://localhost:8000'


class TestSimpleProxy(unittest.TestCase):
    def setUp(self):
        self._proxy_pid = start_proxy(log_output='/dev/null',
                                      log_level='error')
        self._web = start_simplehttp_server()
        time.sleep(.2)
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

    def test_existing_behaviors(self):
        wanted = ['blackout', 'delay', 'dummy', 'error', 'hang', 'transient']
        self.assertEqual(self.client.list_behaviors(), wanted)

    def test_proxy(self):
        # let's do a few simple request first to make sure the proxy works
        self.assertEqual(self.client.get_behavior(), 'dummy')
        for i in range(10):
            res = requests.get(_PROXY)
            self.assertEqual(res.status_code, 200)

        # now let's add a bit of havoc
        with self.client.with_behavior('blackout'):
            # oh look we broke it
            self.assertRaises(requests.ConnectionError, requests.get, _PROXY)
            self.assertEqual(self.client.get_behavior(), 'blackout')

        # we should be back to normal
        self.assertEqual(self.client.get_behavior(), 'dummy')
        res = requests.get(_PROXY)
        self.assertEqual(res.status_code, 200)
