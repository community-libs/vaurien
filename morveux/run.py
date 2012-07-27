import argparse
import sys
import signal

import gevent

from morveux.server import DoWeirdThingsPlease, parse_address
from morveux import __version__


def main():
    parser = argparse.ArgumentParser(description='Runs a mean TCP proxy.')
    parser.add_argument('local', help='Local host and Port', nargs='?')
    parser.add_argument('distant', help='Distant host and port', nargs='?')
    parser.add_argument('--version', action='store_true',
                     default=False, help='Displays Circus version and exits.')

    args = parser.parse_args()

    if args.version:
        print(__version__)
        sys.exit(0)

    if args.local is None or args.distant is None:
        parser.print_usage()
        sys.exit(0)

    # creating the server
    server = DoWeirdThingsPlease(parse_address(args.local),
                                 parse_address(args.distant))

    gevent.signal(signal.SIGTERM, server.close)
    gevent.signal(signal.SIGINT, server.close)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    main()
