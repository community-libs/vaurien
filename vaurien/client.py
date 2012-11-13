import json
from contextlib import contextmanager
from urlparse import urlparse

import requests


class Client(object):
    def __init__(self, host='localhost', port=8080, scheme='http'):
        self.host = host
        self.port = port
        self.scheme = scheme
        self.root_url = '%s://%s:%s' % (scheme, host, port)
        self.handler_url = self.root_url + '/handler'
        self.list_handlers_url = self.root_url + '/handlers'

    def set_handler(self, handler, **options):
        options['name'] = handler
        res = requests.post(self.handler_url, data=json.dumps(options))
        res.raise_for_status()

    def get_handler(self):
        res = requests.get(self.handler_url)
        res.raise_for_status()
        return res.content

    def list_handlers(self):
        res = requests.get(self.list_handlers_url)
        res.raise_for_status()
        return res.json['handlers']

    @contextmanager
    def with_handler(self, handler, **options):
        current = self.get_handler()
        self.set_handler(handler, **options)
        try:
            yield
        finally:
            self.set_handler(current)


def main():
    """Command-line tool to change the handler that's being used by vaurien"""
    import argparse
    parser = argparse.ArgumentParser(description='Change the vaurien handler')
    parser.add_argument('action', help='The action you want to do.',
                        choices=['list-handlers', 'set-handler',
                                 'get-handler'])
    parser.add_argument('handler', nargs='?',
                        help='The vaurien handler to set for the next calls')
    parser.add_argument('--host', dest='host', default='http://localhost:8080',
                        help='The host to use. Provide the scheme.')

    args = parser.parse_args()
    parts = urlparse(args.host)
    scheme = parts.scheme
    host, port = parts.netloc.split(':', -1)
    client = Client(host, port, scheme)
    if args.action == 'list-handlers':
        print ', '.join(client.list_handlers())
    elif args.action == 'set-handler':
        try:
            client.set_handler(args.handler)
            print 'Handler changed to "%s"' % args.handler
        except ValueError:
            print 'The request failed. Please use one of %s' %\
                ', '.join(client.list_handlers())
    elif args.action == 'get-handler':
        print client.get_handler()
