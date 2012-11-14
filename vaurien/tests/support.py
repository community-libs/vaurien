import sys

from vaurien.webserver import create_app

from gevent.wsgi import WSGIServer


class FakeProxy(object):
    """Fake proxy object, to mock the proxy in the tests"""

    def __init__(self, handlers=None):
        self.handlers = handlers or ['default', 'blackout']
        self.handler = 'default'

    def get_handler(self):
        # return None as a callable, since this is for tests only.
        return None, self.handler

    def set_handler(self, name, **options):
        self.handler = name

    def get_handler_names(self):
        return self.handlers


def start_vaurien_httpserver(port):
    """Start a vaurien httpserver, controlling a fake proxy"""
    app = create_app()
    setattr(app, 'proxy', FakeProxy())

    server = WSGIServer(('localhost', int(port)), app)
    server.serve_forever()


if __name__ == '__main__':
    start_vaurien_httpserver(int(sys.argv[1]))
