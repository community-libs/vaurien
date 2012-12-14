from subprocess import Popen
from unittest import TestCase
import sys
import time

from vaurienclient import Client


class TestClient(TestCase):
    def setUp(self):
        port = 8009
        cmd = '%s -m vaurien.tests.support %s' % (sys.executable, port)
        self.process = Popen(cmd.split(' '))

        # wait for the server to start
        time.sleep(1.)
        self.client = Client('localhost', port)

    def tearDown(self):
        self.process.terminate()
        self.process.wait()

    def test_set_valid_behavior(self):
        # check that we don't raise
        self.client.set_behavior('blackout')

    def test_set_invlid_behavior(self):
        self.assertRaises(ValueError, self.client.set_behavior,
                          'invalid_behavior')

    def test_get_default_behavior(self):
        # this should return the default behavior
        self.assertEquals(self.client.get_behavior(), 'default')

    def test_set_and_get_behavior(self):
        # after setting up the behavior, we should retrieve the informations
        # here
        self.client.set_behavior('blackout')
        self.assertEquals(self.client.get_behavior(), 'blackout')

    def test_set_behavior_with_options(self):
        self.client.set_behavior('blackout', foo='foo', bar='bar')
        self.assertEquals(self.client.get_behavior(), 'blackout')

    def test_list_behaviors(self):
        self.assertEquals(self.client.list_behaviors(),
                          ['default', 'blackout'])
