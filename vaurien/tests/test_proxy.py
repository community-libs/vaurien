import unittest
import requests
import subprocess
import sys
import time
import os

from gevent.wsgi import WSGIServer

from vaurien.proxy import OnTheFlyProxy
from vaurien.webserver import app


_CMD = [sys.executable, '-m', 'vaurien.run',
        '--distant', 'google.com:80']


class TestGoogle(unittest.TestCase):
    def setUp(self):
        self._run = subprocess.Popen(_CMD)
        time.sleep(.5)
        if self._run.poll():
            raise ValueError("Could not start the proxy")

    def tearDown(self):
        self._run.terminate()

    def test_proxy(self):
        proxies = {"http": "localhost:8000"}
        res = requests.get("http://google.com", proxies=proxies)
        self.assertEqual(res.status_code, 200)
