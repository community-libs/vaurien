import unittest
import requests
import subprocess
import sys
import time
import os

from gevent.wsgi import WSGIServer

from vaurien.proxy import OnTheFlyProxy
from vaurien.webserver import app
from vaurien.client import Client


_CMD = [sys.executable, '-m', 'vaurien.run',
        '--distant', 'google.com:80',
        '--http']

_PROXY = 'http://localhost:8000'


class TestGoogle(unittest.TestCase):
    def setUp(self):
        self._run = subprocess.Popen(_CMD)
        time.sleep(.5)
        if self._run.poll():
            raise ValueError("Could not start the proxy")
        self.client = Client()

    def tearDown(self):
        self._run.terminate()

    def test_proxy(self):
        # let's do a simple request first to make sure the proxy works
        res = requests.get(_PROXY)
        self.assertEqual(res.status_code, 200)

        # now let's add a bit of havoc
        with self.client.with_handler('errors'):
            # oh look we broke it
            self.assertRaises(requests.ConnectionError, requests.get, _PROXY)

        # we should be back to normal
        res = requests.get(_PROXY)
        self.assertEqual(res.status_code, 200)
