import sys

import gevent
import random

from gevent.server import StreamServer
from gevent.socket import create_connection, gethostbyname

from vaurien.util import import_string, parse_address


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
        behavior = self.settings.getsection('vaurien')['behavior']
        choices = []
        for behavior in behavior.split(','):
            choice = behavior.split(':')
            if len(choice) != 2:
                continue
            percent, handler = choice
            percent = int(percent)
            try:
                handler = import_string(handler)
            except ImportError:
                handler = import_string('vaurien.handlers' + handler)

            choices.append((percent, handler))
            total += int(percent)

        if total != 100:
            raise ValueError('The behavior total needs to be 100')

        for percent, handler in choices:
            self.choices.extend(percent * [handler])

    def handle(self, source, address):
        dest = create_connection(self.dest)
        gevent.spawn(self.weirdify, source, dest, True)
        gevent.spawn(self.weirdify, dest, source, False)

    def statsd_incr(self, counter):
        if self._statsd:
            self._statsd.incr(counter)
        elif self._logger:
            self._logger.info(counter)

    def weirdify(self, source, dest, back):
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
                    handler(source, dest, settings, back)
                except ValueError:
                    return
        finally:
            source.close()
            dest.close()
