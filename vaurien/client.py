from contextlib import contextmanager
import requests


class Client(object):
    def __init__(self, host='localhost', port=8080, scheme='http'):
        self.host = host
        self.port = port
        self.scheme = scheme
        self.handler_url = '%s://%s:%d/handler' % (scheme, host, port)

    def set_next_handler(self, handler):
        res = requests.post(self.handler_url, data=handler)
        if res.status_code != 200 or res.content != 'ok':
            raise ValueError(res.content)

    def get_next_handler(self):
        res = requests.get(self.handler_url)
        if res.status_code != 200:
            raise ValueError(res.content)
        return res.content

    @contextmanager
    def with_handler(self, handler):
        current = self.get_next_handler()
        self.set_next_handler(handler)
        try:
            yield
        finally:
            self.set_next_handler(current)
