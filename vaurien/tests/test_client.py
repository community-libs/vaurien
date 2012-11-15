from subprocess import Popen
from unittest import TestCase
import sys
import time

from vaurien.client import Client


class TestClient(TestCase):
    def setUp(self):
        port = 8009
        cmd = '%s -m vaurien.tests.support %s' % (sys.executable, port)
        self.process = Popen(cmd.split(' '))

        # wait for the server to start
        time.sleep(0.2)
        self.client = Client('localhost', port)

    def tearDown(self):
        self.process.terminate()
        self.process.wait()

    def test_set_valid_handler(self):
        # check that we don't raise
        self.client.set_handler('blackout')

    def test_set_invlid_handler(self):
        self.assertRaises(ValueError, self.client.set_handler,
                          'invalid_handler')

    def test_get_default_handler(self):
        # this should return the default handler
        self.assertEquals(self.client.get_handler(), 'default')

    def test_set_and_get_handler(self):
        # after setting up the handler, we should retrieve the informations
        # here
        self.client.set_handler('blackout')
        self.assertEquals(self.client.get_handler(), 'blackout')

    def test_set_handler_with_options(self):
        self.client.set_handler('blackout', foo='foo', bar='bar')
        self.assertEquals(self.client.get_handler(), 'blackout')

    def test_list_handlers(self):
        self.assertEquals(self.client.list_handlers(),
                          ['default', 'blackout'])
