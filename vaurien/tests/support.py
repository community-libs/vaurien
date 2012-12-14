import sys
import subprocess

from vaurien.webserver import get_config

from gevent.pywsgi import WSGIServer


class FakeProxy(object):
    """Fake proxy object, to mock the proxy in the tests"""

    def __init__(self, behaviors=None):
        self.behaviors = behaviors or ['default', 'blackout']
        self.behavior = 'default'
        self.behavior_options = {}

    def get_behavior(self):
        # return None as a callable, since this is for tests only.
        return None, self.behavior

    def set_behavior(self, name, **options):
        if name not in self.behaviors:
            raise KeyError(name)
        self.behavior = name
        self.behavior_options = options

    def get_behavior_names(self):
        return self.behaviors


def start_vaurien_httpserver(port):
    """Start a vaurien httpserver, controlling a fake proxy"""
    config = get_config()
    config.registry['proxy'] = FakeProxy()

    server = WSGIServer(('localhost', int(port)), config.make_wsgi_app(),
                        log=None)
    server.serve_forever()


def start_simplehttp_server(port=8888):
    cmd = [sys.executable, '-m', 'SimpleHTTPServer', str(port)]
    server = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE)
    return server


if __name__ == '__main__':
    start_vaurien_httpserver(int(sys.argv[1]))
