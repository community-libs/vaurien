import time
import errno
import socket
import gevent
import random

from gevent.server import StreamServer
from gevent.socket import create_connection

from vaurien.util import parse_address, get_handlers_from_config
from vaurien.handlers import handlers as default_handlers, normal


class DefaultProxy(StreamServer):

    def __init__(self, local, distant, handlers=None, protocol=None,
                 settings=None, statsd=None, logger=None, **kwargs):

        if handlers is None:
            handlers = {}
            for handler in default_handlers:
                handlers[handler.__name__] = handler

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
        self.handlers = handlers
        self.handlers.update(get_handlers_from_config(self.settings, logger))
        self.next_handler = normal

    def get_next_handler(self):
        return self.next_handler

    def handle(self, source, address):
        source.setblocking(0)
        dest = create_connection(self.dest)
        dest.setblocking(0)
        handler = self.get_next_handler()
        handler_name = handler.__name__
        self.statsd_incr(handler_name)
        try:
            back = gevent.spawn(self.weirdify, handler, handler_name, source,
                                dest, True)
            forth = gevent.spawn(self.weirdify, handler, handler_name, dest,
                                 source, False)
            back.join()
            forth.join()
        finally:
            source.close()
            dest.close()

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
            settings = self.settings.getsection('handlers.%s' %
                                                    handler_name)
            handler(source=source, dest=dest, to_backend=to_backend,
                    name=handler_name, proxy=self, settings=settings)
        finally:
            self._logger.debug('exiting weirdify %s' % to_backend)

    def get_data(self, source, delay=.2):
        bufsize = int(self.settings['vaurien.bufsize'])
        data = ''
        start = time.time()

        while time.time() - start < delay:
            try:
                data += source.recv(bufsize)
            except socket.error, err:
                if err.args[0] == errno.EWOULDBLOCK:
                    pass

        return data


class RandomProxy(DefaultProxy):

    def __init__(self, *args, **kwargs):
        super(RandomProxy, self).__init__(*args, **kwargs)

        self.choices = []
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

            choices[handler_name] = self.handlers[handler_name], percent
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
            self.choices.extend([self.handlers[name] for i in range(percent)])


    def get_next_handler(self):
        return random.choice(self.choices)


class OnTheFlyProxy(DefaultProxy):

    def set_next_handler(self, handler):
        self.next_handler = self.handlers[handler]
        self._logger.info('next handler changed to "%s"' % handler)
