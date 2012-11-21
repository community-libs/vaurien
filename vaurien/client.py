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
        self.behavior_url = self.root_url + '/behavior'
        self.list_behaviors_url = self.root_url + '/behaviors'

    def set_behavior(self, behavior, **options):
        options['name'] = behavior
        res = requests.put(self.behavior_url, data=json.dumps(options))
        if res.status_code == 400:
            errors = res.json.get('errors', [])
            status = res.json.get('status', 'error')
            if status == 'error' and errors[0]['name'] == 'name':
                raise ValueError(errors[0]['description'])
        res.raise_for_status()

    def get_behavior(self):
        res = requests.get(self.behavior_url)
        res.raise_for_status()
        return res.json['behavior']

    def list_behaviors(self):
        res = requests.get(self.list_behaviors_url)
        res.raise_for_status()
        return res.json['behaviors']

    @contextmanager
    def with_behavior(self, behavior, **options):
        current = self.get_behavior()
        self.set_behavior(behavior, **options)
        try:
            yield
        finally:
            self.set_behavior(current)


def main():
    """Command-line tool to change the behavior that's being used by vaurien"""
    import argparse
    parser = argparse.ArgumentParser(description='Change the vaurien behavior')
    parser.add_argument('action', help='The action you want to do.',
                        choices=['list-behaviors', 'set-behavior',
                                 'get-behavior'])
    parser.add_argument('behavior', nargs='?',
                        help='The vaurien behavior to set for the next calls')
    parser.add_argument('--host', dest='host', default='http://localhost:8080',
                        help='The host to use. Provide the scheme.')

    args = parser.parse_args()
    parts = urlparse(args.host)
    scheme = parts.scheme
    host, port = parts.netloc.split(':', -1)
    client = Client(host, port, scheme)
    if args.action == 'list-behaviors':
        print ', '.join(client.list_behaviors())
    elif args.action == 'set-behavior':
        try:
            client.set_behavior(args.behavior)
            print 'Behavior changed to "%s"' % args.behavior
        except ValueError:
            print 'The request failed. Please use one of %s' %\
                ', '.join(client.list_behaviors())
    elif args.action == 'get-behavior':
        print client.get_behavior()
