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
        '--distant', 'google.com:80',
        '--http']


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

        # let's do a simple request first to make sure the proxy works
        res = requests.get("http://google.com", proxies=proxies)
        self.assertEqual(res.status_code, 200)

        # now let's add a bit of havoc -
        res = requests.post("http://localhost:8080/handler", data='errors')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, 'ok')

        # oh look we broke it
        self.assertRaises(requests.ConnectionError, requests.get,
                          "http://google.com", proxies=proxies)

        # let's unbreak it
        res = requests.post("http://localhost:8080/handler", data='normal')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.content, 'ok')

        # we should be back to normal
        res = requests.get("http://google.com", proxies=proxies)
        self.assertEqual(res.status_code, 200)

