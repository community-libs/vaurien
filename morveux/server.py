import sys

from statsd import StatsdClient

import gevent
import random

from gevent.server import StreamServer
from gevent.socket import create_connection, gethostbyname


class DoWeirdThingsPlease(StreamServer):

    def __init__(self, listener, dest, protocol=None, config=None, **kwargs):
        StreamServer.__init__(self, listener, **kwargs)
        self.dest = dest
        self.config = config
        self.prococol = protocol
        self.running = True
        self.statsd = StatsdClient(host=config.get('host', '127.0.0.1'),
                                   port=config.get('port', 8125),
                                   prefix=config.get('prefix', 'morveux'),
                                   sample_rate=config.get('sample_rate', 1.0))
        self.choices = []
        self.initialize_choices()

    def initialize_choices(self):
        total = 0
        for key, value in self.config.items():
            if key.endswith('ratio'):
                total += value
                if total > 100:
                    print "cumulative ratios need to be < 100"
                    sys.exit(1)

                case = 'handle_%s' % key[:-len('_ratio')]
                if not hasattr(self, case):
                    print "we don't know how to handle %s" % case
                    sys.exit(1)

                self.choices.extend(value * [getattr(self, case)])

    def handle(self, source, address):
        self.statsd.incr('proxied')
        dest = create_connection(self.dest)
        gevent.spawn(self.weirdify, source, dest)
        gevent.spawn(self.weirdify, dest, source)

    def _get_data(self, source):
        data = source.recv(1024)
        if not data:
            raise ValueError
        return data

    def weirdify(self, source, dest):
        """This is where all the magic happens.

        Depending the configuration, we will chose to either drop packets,
        proxy them, wait a long time, etc, as defined in the configuration.
        """
        try:
            while self.running:
                # chose what we want to do.
                handler = random.choice(self.choices)
                print(handler.__name__)
                try:
                    handler(source, dest)
                except ValueError:
                    return
        finally:
            source.close()
            dest.close()

    def handle_proxy(self, source, dest):
        dest.sendall(self._get_data(source))

    def handle_delay(self, source, dest):
        gevent.sleep(self.config['sleep_delay'])
        self.handle_proxy(source, dest)

    def handle_errors(self, source, dest):
        """Throw errors on the socket"""
        self.__get_data(source)  # don't do anything with the data
        # XXX find how to handle errors (which errors should we send)
        dest.sendall("YEAH")

    def handle_blackout(self, source, dest):
        """just drop the packets that had been sent"""
        # consume the socket. That's it.
        self._get_data(source)


def parse_address(address):
    try:
        hostname, port = address.rsplit(':', 1)
        port = int(port)
    except ValueError:
        sys.exit('Expected HOST:PORT: %r' % address)
    return gethostbyname(hostname), port
