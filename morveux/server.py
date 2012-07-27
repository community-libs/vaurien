import sys
import signal

import gevent
from gevent.server import StreamServer
from gevent.socket import create_connection, gethostbyname


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
    args = sys.argv[1:]
    if len(args) != 2:
        sys.exit('Usage: %s localhost:port destination:port' % __file__)
    source = parse_address(args[0])
    dest = parse_address(args[1])
    server = DoWeirdThingsPlease(source, dest)
    gevent.signal(signal.SIGTERM, server.close)
    gevent.signal(signal.SIGINT, server.close)
    server.serve_forever()

if __name__ == '__main__':
    main()
