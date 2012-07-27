import sys
import signal
import argparse

import gevent
from gevent.server import StreamServer
from gevent.socket import create_connection, gethostbyname

from morveux import __version__


class DoWeirdThingsPlease(StreamServer):

    def __init__(self, listener, dest, **kwargs):
        StreamServer.__init__(self, listener, **kwargs)
        self.dest = dest

    def handle(self, source, address):
        try:
            dest = create_connection(self.dest)
        except IOError:
            return
        gevent.spawn(forward, source, dest)
        gevent.spawn(forward, dest, source)

    def close(self):
        if self.closed:
            sys.exit('Multiple exit signals received - aborting.')
        else:
            StreamServer.close(self)


def forward(source, dest):
    try:
        while True:
            data = source.recv(1024)
            if not data:
                break
            dest.sendall(data)
    finally:
        source.close()
        dest.close()


def parse_address(address):
    try:
        hostname, port = address.rsplit(':', 1)
        port = int(port)
    except ValueError:
        sys.exit('Expected HOST:PORT: %r' % address)
    return gethostbyname(hostname), port


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
