import argparse
import sys
import logging

from vaurien.proxy import OnTheFlyProxy, RandomProxy
from vaurien.config import load_into_settings, DEFAULT_SETTINGS
from vaurien import __version__, logger
from vaurien.behaviors import get_behaviors
from vaurien.protocols import get_protocols


LOG_LEVELS = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG}

LOG_FMT = r"%(asctime)s [%(process)d] [%(levelname)s] %(message)s"
LOG_DATE_FMT = r"%Y-%m-%d %H:%M:%S"


class DevNull(object):
    def write(self, msg):
        pass


def close_on_exec(fd):
    try:
        import fcntl
    except ImportError:
        return

    flags = fcntl.fcntl(fd, fcntl.F_GETFD)
    flags |= fcntl.FD_CLOEXEC
    fcntl.fcntl(fd, fcntl.F_SETFD, flags)


def configure_logger(logger, level='INFO', output="-"):
    loglevel = LOG_LEVELS.get(level.lower(), logging.INFO)
    logger.setLevel(loglevel)
    if output == "-":
        h = logging.StreamHandler()
    else:
        h = logging.FileHandler(output)
        close_on_exec(h.stream.fileno())
    fmt = logging.Formatter(LOG_FMT, LOG_DATE_FMT)
    h.setFormatter(fmt)
    logger.addHandler(h)


def get_statsd_from_settings(settings):
    if settings['enabled']:
        from statsd import StatsdClient
        statsd = StatsdClient(host=settings['host'],
                              port=settings['port'],
                              prefix=settings['prefix'],
                              sample_rate=settings['sample_rate'])
    else:
        statsd = None
    return statsd


def build_args(parser, items, prefix):
    for name, klass in items:
        for option_name, option in klass.options.items():
            if len(option) == 3:
                description, type_, default = option
                choices = None
            else:
                description, type_, default, choices = option

            option_name = '--%s-%s-%s' % (prefix, name,
                                          option_name.replace('_', '-'))
            if type_ is bool:
                kws = {'action': 'store_true'}
            else:
                kws = {'action': 'store', 'type': type_}

            if choices is not None:
                kws = {'choices': choices}

            parser.add_argument(option_name, default=default,
                                help=description, **kws)


def main():
    # get the values from the default config
    defaults = DEFAULT_SETTINGS.items()
    defaults.sort()

    parser = argparse.ArgumentParser(description='Runs a Chaos TCP proxy.')

    # other arguments
    parser.add_argument('--config', help='Configuration file', default=None)
    parser.add_argument('--version', action='store_true', default=False,
                        help='Displays version and exits.')
    parser.add_argument('--http', action='store_true', default=False,
                        help='Start a simple http server to control vaurien')
    parser.add_argument('--http-host', default='localhost',
                        help='Host of the http server, if any')
    parser.add_argument('--http-port', default=8080, type=int,
                        help='Port of the http server, if any')
    parser.add_argument('--protocol', default='tcp', choices=get_protocols(),
                        help='Protocol used')

    for key, default in defaults:
        if key.startswith('vaurien'):
            key = key[len('vaurien.'):]
        key = key.replace('_', '-')
        type_ = default.__class__
        if type_ is bool:
            parser.add_argument('--%s' % key, default=default,
                                action='store_true')
        else:
            parser.add_argument('--%s' % key, default=default,
                                type=type_)

    parser.add_argument('--log-level', dest='loglevel', default='info',
                        choices=LOG_LEVELS.keys() + [key.upper() for key in
                                                     LOG_LEVELS.keys()],
                        help="log level")
    parser.add_argument('--log-output', dest='logoutput', default='-',
                        help="log output")

    # now for each registered behavior, we are going to provide its options
    build_args(parser, get_behaviors().items(), 'behavior')

    # same thing for the protocols
    build_args(parser, get_protocols().items(), 'protocol')

    # parsing the provided args
    args = parser.parse_args()

    if args.version:
        print(__version__)
        sys.exit(0)

    # configure the logger
    configure_logger(logger, args.loglevel, args.logoutput)

    # load the defaults
    settings = DEFAULT_SETTINGS.copy()

    # overwrite with the command line arguments
    for key in settings.keys():
        prefix = ''
        if key.startswith('vaurien'):
            key = key[len('vaurien.'):]
            prefix = 'vaurien.'

        try:
            value = getattr(args, key)
        except AttributeError:
            value = None

        if value is not None:
            settings[prefix + key] = value

    # overwrite with the config file if any
    if args.config is not None:
        try:
            load_into_settings(args.config, settings)
        except ValueError, e:
            print(e)
            sys.exit(1)

    # pass the args in the settings
    settings['args'] = args
    statsd = get_statsd_from_settings(settings.getsection('statsd'))

    # creating the proxy
    proxy_args = dict(proxy=settings['vaurien.proxy'],
                      backend=settings['vaurien.backend'],
                      settings=settings, statsd=statsd, logger=logger,
                      protocol=args.protocol)

    if args.http:
        # if we are using the http server, then we want to use the OnTheFly
        # proxy
        proxy = OnTheFlyProxy(**proxy_args)
        from vaurien.webserver import get_config
        from gevent.pywsgi import WSGIServer

        config = get_config()
        config.registry['proxy'] = proxy
        app = config.make_wsgi_app()

        # configure the web app logger
        # configure_logger(app.logger, args.loglevel, args.logoutput)

        # app.run(host=args.http_host, port=args.http_port)
        http_server = WSGIServer((args.http_host, args.http_port), app,
                                 log=DevNull())

        http_server.start()
        logger.info('Started the HTTP server: http://%s:%s' %
                    (args.http_host, args.http_port))
    else:
        # per default, we want to randomize
        proxy = RandomProxy(**proxy_args)

    try:
        proxy.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
    finally:
        logger.info('Bye!')


if __name__ == '__main__':
    main()
