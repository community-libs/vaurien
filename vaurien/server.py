import sys

import gevent
import random

from gevent.server import StreamServer
from gevent.socket import create_connection, gethostbyname


class DoWeirdThingsPlease(StreamServer):

    def __init__(self, local, distant, protocol=None, settings=None,
                 statsd=None, logger=None, **kwargs):

        logger.info('Starting the mean proxy server')
        logger.info('%s => %s' % (local, distant))

        local = parse_address(local)
        dest = parse_address(distant)

        StreamServer.__init__(self, local, **kwargs)

        self.dest = dest
        self.settings = settings
        self.prococol = protocol
        self.running = True
        self._statsd = statsd
        self._logger = logger
        self.choices = []
        self.initialize_choices()

    def initialize_choices(self):
        total = 0
        for key, value in self.settings.getsection('vaurien').items():
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
        dest = create_connection(self.dest)
        gevent.spawn(self.weirdify, source, dest)
        gevent.spawn(self.weirdify, dest, source)

    def _get_data(self, source):
        data = source.recv(1024)
        if not data:
            raise ValueError
        return data

    def statsd_incr(self, counter):
        if self._statsd:
            self._statsd.incr(counter)
        elif self._logger:
            self._logger.info(counter)

    def weirdify(self, source, dest):
        """This is where all the magic happens.

        Depending the configuration, we will chose to either drop packets,
        proxy them, wait a long time, etc, as defined in the configuration.
        """
        try:
            while self.running:
                # chose what we want to do.
                handler = random.choice(self.choices)
                self.statsd_incr(handler.__name__)
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
        gevent.sleep(self.settings['vaurien.sleep_delay'])
        self.handle_proxy(source, dest)

    def handle_errors(self, source, dest):
        """Throw errors on the socket"""
        self._get_data(source)  # don't do anything with the data
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
