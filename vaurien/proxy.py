import time
import errno
import socket
import gevent
import random
from select import select

from gevent.server import StreamServer
from gevent.socket import create_connection

from vaurien.util import parse_address, get_handlers_from_config
from vaurien.handlers import handlers as default_handlers


class DefaultProxy(StreamServer):

    def __init__(self, local, distant, handlers=None, protocol=None,
                 settings=None, statsd=None, logger=None, **kwargs):

        if handlers is None:
            handlers = default_handlers
        logger.info('Starting the Chaos TCP Server')
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
        self.handler = default_handlers['dummy']
        self.handler_name = 'dummy'

    def get_handler(self):
        return self.handler, self.handler_name

    def handle(self, source, address):
        source.setblocking(0)
        dest = create_connection(self.dest)
        dest.setblocking(0)
        handler, handler_name = self.get_handler()
        self.statsd_incr(handler_name)

        while True:
            try:
                rlist, __, __ = select([source, dest], [], [], 30)
            except socket.error, err:
                rlist = []

            if rlist == []:
                break

            greens = []
            for sock in rlist:
                if sock == source:
                    greens.append(gevent.spawn(self.weirdify, handler, handler_name,
                                               source, dest, True))
                else:
                    greens.append(gevent.spawn(self.weirdify, handler, handler_name,
                                               dest, source, False))

            for green in greens:
                green.join()

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
            settings = self.settings.getsection('handlers.%s' % handler_name)
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
            if 'dummy' in choices:
                choices['dummy'][1] += missing
            else:
                choices['dummy'] = default_handlers['dummy'], missing

        for name, (handler, percent) in choices.items():
            self.choices.extend(
                [(self.handlers[name], name) for i in range(percent)])

    def get_handler(self):
        return random.choice(self.choices)


class OnTheFlyProxy(DefaultProxy):

    def set_handler(self, handler):
        self.handler = self.handlers[handler]
        self.handler_name = handler
        self._logger.info('Handler changed to "%s"' % handler)
