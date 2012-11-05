import fcntl
import argparse
import sys
import logging

from vaurien.proxy import OnTheFlyProxy, RandomProxy
from vaurien.config import load_into_settings, DEFAULT_SETTINGS
from vaurien import __version__, logger


LOG_LEVELS = {
    "critical": logging.CRITICAL,
    "error": logging.ERROR,
    "warning": logging.WARNING,
    "info": logging.INFO,
    "debug": logging.DEBUG}

LOG_FMT = r"%(asctime)s [%(process)d] [%(levelname)s] %(message)s"
LOG_DATE_FMT = r"%Y-%m-%d %H:%M:%S"


def close_on_exec(fd):
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


def main():
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

    # get the values from the default config
    keys = DEFAULT_SETTINGS.keys()
    keys.sort()

    for key in keys:
        if key.startswith('vaurien'):
            key = key[len('vaurien.'):]

        parser.add_argument('--%s' % key, default=None)

    parser.add_argument('--log-level', dest='loglevel', default='info',
            choices=LOG_LEVELS.keys() + [key.upper() for key in
                LOG_LEVELS.keys()],
            help="log level")
    parser.add_argument('--log-output', dest='logoutput', default='-',
            help="log output")

    args, remaining = parser.parse_known_args()

    if args.version:
        print(__version__)
        sys.exit(0)

    # configure the logger
    configure_logger(logger, args.loglevel, args.logoutput)

    settings = DEFAULT_SETTINGS.copy()

    if args.config is not None:
        # read the config if provided
        try:
            load_into_settings(args.config, settings)
        except ValueError, e:
            print(e)
            sys.exit(1)

    # overwrite with the commandline arguments
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

    # inject custom handlers options
    for option in remaining:
        if not option.startswith('--handlers.'):
            continue
        option = option[len('--'):]
        option = option.split('=', 1)
        settings[option[0]] = option[1]

    statsd = get_statsd_from_settings(settings.getsection('statsd'))

    # creating the proxy
    proxy_args = dict(local=settings['vaurien.local'],
                      distant=settings['vaurien.distant'],
                      settings=settings, statsd=statsd, logger=logger)


    if args.http:
        # if we are using the http server, then we want to use the OnTheFly
        # proxy
        proxy = OnTheFlyProxy(**proxy_args)
        from vaurien.webserver import app
        from gevent.wsgi import WSGIServer

        setattr(app, 'proxy', proxy)
        # app.run(host=args.http_host, port=args.http_port)
        http_server = WSGIServer((args.http_host, args.http_port), app)
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
