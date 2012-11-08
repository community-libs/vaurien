import gevent
import random

from gevent.server import StreamServer
from gevent.socket import create_connection
from gevent.select import select, error

from vaurien.util import parse_address, get_handlers_from_config
from vaurien.handlers import handlers as default_handlers
from vaurien._pool import FactoryPool


class DefaultProxy(StreamServer):

    def __init__(self, proxy, backend, handlers=None, protocol=None,
                 settings=None, statsd=None, logger=None, timeout=30,
                 **kwargs):

        if handlers is None:
            handlers = default_handlers
        logger.info('Starting the Chaos TCP Server')
        logger.info('%s => %s' % (proxy, backend))

        proxy = parse_address(proxy)
        dest = parse_address(backend)
        StreamServer.__init__(self, proxy, **kwargs)

        self._pool = FactoryPool(self._create_connection)
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
        self.timeout = timeout

    def _create_connection(self):
        conn = create_connection(self.dest)
        conn.setblocking(0)
        return conn

    def get_handler(self):
        return self.handler, self.handler_name

    def handle(self, client_sock, address):
        client_sock.setblocking(0)
        handler, handler_name = self.get_handler()
        handler.proxy = self
        handler.logger = self._logger
        self.statsd_incr(handler_name)
        try:
            with self._pool.reserve() as backend_sock:
                while True:
                    try:
                        res = select([client_sock, backend_sock], [], [],
                                     timeout=self.timeout)
                        rlist = res[0]
                    except error:
                        return

                    greens = [gevent.spawn(self.weirdify, handler, client_sock,
                                           backend_sock,
                                           sock is not backend_sock,
                                           handler_name)
                              for sock in rlist]

                    res = [green.get() for green in greens]

                    if not all(res):
                        return

        finally:
            client_sock.close()

    def statsd_incr(self, counter):
        if self._statsd:
            self._statsd.incr(counter)
        elif self._logger:
            self._logger.info(counter)

    def weirdify(self, handler, client_sock, backend_sock, to_backend,
                 handler_name):
        """This is where all the magic happens.

        Depending the configuration, we will chose to either drop packets,
        proxy them, wait a long time, etc, as defined in the configuration.
        """
        self._logger.debug('starting weirdify %s' % to_backend)
        try:
            settings = self.settings.getsection('handlers.%s' % handler_name)
            handler.update_settings(settings)
            return handler(client_sock=client_sock, backend_sock=backend_sock,
                           to_backend=to_backend)
        finally:
            self._logger.debug('exiting weirdify %s' % to_backend)


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
            if handler_name not in self.handlers:
                choices = self.handlers.keys()
                msg = "%r is an unknown handler. Pick one of: %s."
                raise ValueError(msg % (handler_name,
                                        ', '.join(['%r' % choice
                                                   for choice in choices])))

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

    def set_handler(self, **options):
        handler_name = options.pop('name')
        self.handler = self.handlers[handler_name]
        self.handler_name = handler_name

        for name, value in options.items():
            self.handler.settings[name] = value

        self._logger.info('Handler changed to "%s"' % handler_name)
