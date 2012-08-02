import gevent
import random

from gevent.server import StreamServer
from gevent.socket import create_connection, error

from vaurien.util import import_string, parse_address
from vaurien.handlers import normal


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
        self.handlers = {}
        self.initialize_choices()

    def initialize_choices(self):
        total = 0
        behavior = self.settings.getsection('vaurien')['behavior']
        choices = {}

        for behavior in behavior.split(','):
            choice = behavior.split(':')
            if len(choice) != 2:
                raise ValueError('You need to use name:percentage')

            percent, handler_name = choice
            percent = int(percent)

            # have a look if we have a section named handler:{handler}
            self.settings.getsection('handler:%s' % handler_name)

            # import from the python path, fallback on vaurien handlers
            try:
                handler = import_string(handler_name)
            except ImportError:
                handler = import_string('vaurien.handlers.' + handler_name)

            choices[handler_name] = handler, percent
            total += percent

        if total > 100:
            raise ValueError('The behavior total needs to be 100 or less')
        elif total < 100:
            missing = 100 - total
            if 'normal' in choices:
                choices['normal'][1] += missing
            else:
                choices['normal'] = normal, missing

        for name, (handler, percent) in choices.items():
            self.choices.extend(percent * [name])
            self.handlers[name] = handler

    def handle(self, source, address):
        dest = create_connection(self.dest)
        handler_name = random.choice(self.choices)
        handler = self.handlers[handler_name]
        self.statsd_incr(handler_name)
        gevent.spawn(self.weirdify, handler, handler_name, source, dest, True)
        gevent.spawn(self.weirdify, handler, handler_name, dest, source, False)

    def statsd_incr(self, counter):
        if self._statsd:
            self._statsd.incr(counter)
        elif self._logger:
            self._logger.info(counter)

    def weirdify(self, handler, handler_name, source, dest, to_backend):
        """This is where all the magic happens.

        Depending the configuration, we will chose to either drop packets,
        proxy them, wait a long time, etc, as defined in the configuration.
        """
        self._logger.debug('starting weirdify %s' % to_backend)
        try:
            while self.running:
                # chose what we want to do.
                try:
                    settings = self.settings.getsection('handlers:%s' %
                                                        handler_name)
                    handler(source=source, dest=dest, to_backend=to_backend,
                            name=handler_name, server=self, settings=settings)
                except ValueError:
                    return
        finally:
            source.close()
            dest.close()
            self._logger.debug('exiting weirdify %s' % to_backend)

    def get_data(self, source):
        try:
            data = source.recv(int(self.settings['vaurien.bufsize']))
            if not data:
                raise ValueError
            return data
        except error:  # socket.error
            raise ValueError
