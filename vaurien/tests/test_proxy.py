import unittest
import requests
import subprocess
import sys
import time

from vaurien.client import Client
from vaurien.util import start_proxy, stop_proxy


_PROXY = 'http://localhost:8000'
_SERVER = [sys.executable, '-m', 'SimpleHTTPServer',
           '8888']


class TestGoogle(unittest.TestCase):
    def setUp(self):
        self._proxy_pid = start_proxy()
        self._web = subprocess.Popen(_SERVER)
        time.sleep(.5)
        if self._web.poll():
            raise ValueError("Could not start the proxy")

        self.client = Client()

    def tearDown(self):
        stop_proxy(self._proxy_pid)
        self._web.terminate()

    def test_proxy(self):
        # let's do a simple request first to make sure the proxy works
        res = requests.get(_PROXY)
        self.assertEqual(res.status_code, 200)

        # now let's add a bit of havoc
        with self.client.with_handler('blackout'):
            # oh look we broke it
            self.assertRaises(requests.ConnectionError, requests.get, _PROXY)

        # we should be back to normal
        res = requests.get(_PROXY)
        self.assertEqual(res.status_code, 200)
