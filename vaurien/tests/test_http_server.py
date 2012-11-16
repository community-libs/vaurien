from unittest import TestCase
import json

from vaurien.webserver import create_app
from vaurien.tests.support import FakeProxy


class TestHTTPServer(TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        setattr(self.app, 'proxy', FakeProxy())
        self.client = self.app.test_client()

    def tearDown(self):
        self.app = None

    def assertJSONEquals(self, res, value, status=200):
        self.assertEquals(res.headers['Content-Type'], 'application/json')
        self.assertEquals(res.status_code, status)
        self.assertEquals(json.loads(res.data), value)

    def test_behaviors_are_returned(self):
        # the behaviors should be returned as a list of behaviors, in json.
        res = self.client.get('/behaviors')
        self.assertJSONEquals(res, {'behaviors': ['default', 'blackout']})

    def test_get_behavior(self):
        # test that we can know what is the behavior currently used
        res = self.client.get('/behavior')
        self.assertJSONEquals(res, {'behavior': self.app.proxy.behavior})

    def test_set_unknown_behavior(self):
        # we shuld get errors back from the server if we try to set a behavior
        # which doesn't exist
        behavior = {'name': 'doesnt_exist'}
        res = self.client.post('/behavior', data=json.dumps(behavior))
        self.assertEquals(res.headers['Content-Type'], 'application/json')
        self.assertEquals(res.status_code, 400)
        errors = json.loads(res.data)
        self.assertEquals(errors['status'], 'error')
        self.assertEquals(len(errors['errors']), 1)
        self.assertEquals(errors['errors'][0]['location'], 'body')
        self.assertEquals(errors['errors'][0]['name'], 'name')

    def test_set_valid_behavior_name(self):
        # it's possible to only set a behavior with its name
        behavior_name = self.app.proxy.behaviors[-1]
        behavior = {'name': behavior_name}
        res = self.client.post('/behavior', data=json.dumps(behavior))
        self.assertJSONEquals(res, {'status': 'ok'})
        self.assertEquals(self.app.proxy.behavior, behavior_name)

    def test_set_valid_behavior_with_options(self):
        # it's possible to pass options with the behavior
        behavior_name = self.app.proxy.behaviors[-1]
        behavior = {'name': behavior_name}
        behavior_options = {'foo': 'bar', 'baz': 'babar'}
        behavior.update(behavior_options)
        res = self.client.post('/behavior', data=json.dumps(behavior))
        self.assertJSONEquals(res, {'status': 'ok'})
        self.assertEquals(self.app.proxy.behavior, behavior_name)
        self.assertEquals(self.app.proxy.behavior_options, behavior_options)
