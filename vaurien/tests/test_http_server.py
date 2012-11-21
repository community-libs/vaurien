from unittest import TestCase

import webtest

from vaurien.webserver import get_config
from vaurien.tests.support import FakeProxy


class TestHTTPServer(TestCase):
    def setUp(self):
        self.config = get_config()
        self.proxy = FakeProxy()
        self.config.registry['proxy'] = self.proxy

        self.app = self.config.make_wsgi_app()
        self.client = webtest.TestApp(self.app)

    def tearDown(self):
        self.app = None

    def test_behaviors_are_returned(self):
        # the behaviors should be returned as a list of behaviors, in json.
        res = self.client.get('/behaviors')
        self.assertEquals(res.json, {'behaviors': ['default', 'blackout']})

    def test_get_behavior(self):
        # test that we can know what is the behavior currently used
        res = self.client.get('/behavior')
        self.assertEquals(res.json, {'behavior': self.proxy.behavior})

    def test_set_unknown_behavior(self):
        # we should get errors back from the server if we try to set a behavior
        # which doesn't exist
        res = self.client.put_json('/behavior', {'name': 'doesnt_exist'},
                                   status=400)
        errors = res.json
        self.assertEquals(errors['status'], 'error')
        self.assertEquals(len(errors['errors']), 1)
        self.assertEquals(errors['errors'][0]['location'], 'body')
        self.assertEquals(errors['errors'][0]['name'], 'name')

    def test_set_valid_behavior_name(self):
        # it's possible to only set a behavior with its name
        behavior_name = self.proxy.behaviors[-1]
        res = self.client.put_json('/behavior', {'name': behavior_name})
        self.assertEquals(res.json, {'status': 'ok'})
        self.assertEquals(self.proxy.behavior, behavior_name)

    def test_set_valid_behavior_with_options(self):
        # it's possible to pass options with the behavior
        behavior_name = self.proxy.behaviors[-1]
        behavior = {'name': behavior_name}
        behavior_options = {'foo': 'bar', 'baz': 'babar'}
        behavior.update(behavior_options)
        res = self.client.put_json('/behavior', behavior)
        self.assertEquals(res.json, {'status': 'ok'})
        self.assertEquals(self.proxy.behavior, behavior_name)
        self.assertEquals(self.proxy.behavior_options, behavior_options)
