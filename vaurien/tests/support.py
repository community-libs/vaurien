import sys
import subprocess

from vaurien.webserver import create_app

from gevent.wsgi import WSGIServer


class FakeProxy(object):
    """Fake proxy object, to mock the proxy in the tests"""

    def __init__(self, handlers=None):
        self.handlers = handlers or ['default', 'blackout']
        self.handler = 'default'
        self.handler_options = {}

    def get_handler(self):
        # return None as a callable, since this is for tests only.
        return None, self.handler

    def set_handler(self, name, **options):
        if name not in self.handlers:
            raise KeyError(name)
        self.handler = name
        self.handler_options = options

    def get_handler_names(self):
        return self.handlers


def start_vaurien_httpserver(port):
    """Start a vaurien httpserver, controlling a fake proxy"""
    app = create_app()
    setattr(app, 'proxy', FakeProxy())

    server = WSGIServer(('localhost', int(port)), app, log=None)
    server.serve_forever()


def start_simplehttp_server(port=8888):
    cmd = [sys.executable, '-m', 'SimpleHTTPServer', str(port)]
    server = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    return server


if __name__ == '__main__':
    start_vaurien_httpserver(int(sys.argv[1]))
