import gevent
import random
from uuid import uuid4

from gevent.server import StreamServer
from gevent.socket import create_connection
from gevent.select import select, error

from vaurien.util import parse_address, get_behaviors_from_config
from vaurien.protocols import get_protocols
from vaurien.behaviors import get_behaviors

from vaurien._pool import FactoryPool


class DefaultProxy(StreamServer):

    def __init__(self, proxy, backend, protocol='tcp', behaviors=None,
                 settings=None, statsd=None, logger=None, **kwargs):
        self.settings = settings
        cfg = self.settings.getsection('vaurien')

        if behaviors is None:
            behaviors = get_behaviors()

        logger.info('Starting the Chaos TCP Server')
        parsed_proxy = parse_address(proxy)
        dest = parse_address(backend)
        StreamServer.__init__(self, parsed_proxy, **kwargs)
        self.pool_max_size = cfg.get('pool_max_size', 100)
        self.pool_timeout = cfg.get('pool_timeout', 30)
        self.async_mode = cfg.get('async_mode', False)
        self._pool = FactoryPool(self._create_connection, self.pool_max_size,
                                 self.pool_timeout)
        self.dest = dest
        self.running = True
        self._statsd = statsd
        self._logger = logger
        self.behaviors = behaviors
        self.behaviors.update(get_behaviors_from_config(self.settings, logger))
        self.behavior = get_behaviors()['dummy']
        self.behavior_name = 'dummy'
        self.stay_connected = cfg.get('stay_connected', False)
        self.timeout = cfg.get('timeout', 30)
        self.protocol = cfg.get('protocol', protocol)
        self.handler = get_protocols()[self.protocol]

        logger.info('Options:')
        logger.info('* proxies from %s to %s' % (proxy, backend))
        logger.info('* timeout: %d' % self.timeout)
        logger.info('* stay_connected: %d' % self.stay_connected)
        logger.info('* pool_max_size: %d' % self.pool_max_size)
        logger.info('* pool_timeout: %d' % self.pool_timeout)
        logger.info('* async_mode: %d' % self.async_mode)

    def _create_connection(self):
        conn = create_connection(self.dest)
        if self.async_mode:
            conn.setblocking(0)
        return conn

    def get_behavior(self):
        return self.behavior, self.behavior_name

    def get_behavior_names(self):
        keys = get_behaviors().keys()
        keys.sort()
        return keys

    def handle(self, client_sock, address):
        client_sock.setblocking(0)
        behavior, behavior_name = self.get_behavior()

        statsd_prefix = '%s.%s.' % (self.protocol, uuid4())
        self.statsd_incr(statsd_prefix + 'start')

        try:
            with self._pool.reserve() as backend_sock:
                while True:
                    try:
                        res = select([client_sock, backend_sock], [], [],
                                     timeout=self.timeout)
                        rlist = res[0]
                    except error:
                        backend_sock.close()
                        backend_sock._closed = True
                        return

                    greens = [gevent.spawn(self._weirdify,
                                           client_sock, backend_sock,
                                           sock is not backend_sock,
                                           statsd_prefix,
                                           behavior, behavior_name)
                              for sock in rlist]

                    res = [green.get() for green in greens]

                    got_data = all(res) and len(res) > 0

                    if not got_data and not self.stay_connected:
                        return

        finally:
            self.statsd_incr(statsd_prefix + 'end')
            client_sock.close()

    def statsd_incr(self, counter):
        if self._statsd:
            self._statsd.incr(counter)
        elif self._logger:
            self._logger.info(counter)

    def _weirdify(self, client_sock, backend_sock, to_backend,
                  statsd_prefix, behavior, behavior_name):
        """This is where all the magic happens.

        Depending the configuration, we will chose to either drop packets,
        proxy them, wait a long time, etc, as defined in the configuration.
        """
        if to_backend:
            self.statsd_incr(statsd_prefix + 'to_backend')
            dest = backend_sock
            source = client_sock
        else:
            self.statsd_incr(statsd_prefix + 'to_client')
            source = backend_sock
            dest = client_sock

        self._logger.debug('starting weirdify %s' % to_backend)
        try:
            # XXX cache this ?
            args = self.settings['args']
            behavior_settings = {}
            prefix = 'behavior_%s_' % behavior_name
            for arg in dir(args):
                if not arg.startswith(prefix):
                    continue
                behavior_settings[arg[len(prefix):]] = getattr(args, arg)

            behavior.update_settings(behavior_settings)

            # calling the handler
            return self.handler(source, dest, to_backend, behavior)
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

            percent, behavior_name = choice
            percent = int(percent)
            if behavior_name not in self.behaviors:
                choices = self.behaviors.keys()
                msg = "%r is an unknown behavior. Pick one of: %s."
                raise ValueError(msg % (behavior_name,
                                        ', '.join(['%r' % choice
                                                   for choice in choices])))

            choices[behavior_name] = self.behaviors[behavior_name], percent
            total += percent

        if total > 100:
            raise ValueError('The behavior total needs to be 100 or less')
        elif total < 100:
            missing = 100 - total
            if 'dummy' in choices:
                choices['dummy'][1] += missing
            else:
                choices['dummy'] = get_behaviors()['dummy'], missing

        for name, (behavior, percent) in choices.items():
            self.choices.extend(
                [(self.behaviors[name], name) for i in range(percent)])

    def get_behavior(self):
        return random.choice(self.choices)


class OnTheFlyProxy(DefaultProxy):

    def set_behavior(self, **options):
        behavior_name = options.pop('name')
        self.behavior = self.behaviors[behavior_name]
        self.behavior_name = behavior_name
        for name, value in options.items():
            self.behavior.settings[name] = value
        self._logger.info('Handler changed to "%s"' % behavior_name)
