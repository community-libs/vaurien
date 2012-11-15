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

    def test_handlers_are_returned(self):
        # the handlers should be returned as a list of handlers, in json.
        res = self.client.get('/handlers')
        self.assertJSONEquals(res, {'handlers': ['default', 'blackout']})

    def test_get_handler(self):
        # test that we can know what is the handler currently used
        res = self.client.get('/handler')
        self.assertJSONEquals(res, {'handler': self.app.proxy.handler})

    def test_set_unknown_handler(self):
        # we shuld get errors back from the server if we try to set a handler
        # which doesn't exist
        handler = {'name': 'doesnt_exist'}
        res = self.client.post('/handler', data=json.dumps(handler))
        self.assertEquals(res.headers['Content-Type'], 'application/json')
        self.assertEquals(res.status_code, 400)
        errors = json.loads(res.data)
        self.assertEquals(errors['status'], 'error')
        self.assertEquals(len(errors['errors']), 1)
        self.assertEquals(errors['errors'][0]['location'], 'body')
        self.assertEquals(errors['errors'][0]['name'], 'name')

    def test_set_valid_handler_name(self):
        # it's possible to only set a handler with its name
        handler_name = self.app.proxy.handlers[-1]
        handler = {'name': handler_name}
        res = self.client.post('/handler', data=json.dumps(handler))
        self.assertJSONEquals(res, {'status': 'ok'})
        self.assertEquals(self.app.proxy.handler, handler_name)

    def test_set_valid_handler_with_options(self):
        # it's possible to pass options with the handler
        handler_name = self.app.proxy.handlers[-1]
        handler = {'name': handler_name}
        handler_options = {'foo': 'bar', 'baz': 'babar'}
        handler.update(handler_options)
        res = self.client.post('/handler', data=json.dumps(handler))
        self.assertJSONEquals(res, {'status': 'ok'})
        self.assertEquals(self.app.proxy.handler, handler_name)
        self.assertEquals(self.app.proxy.handler_options, handler_options)
