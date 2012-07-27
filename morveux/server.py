import sys
import gevent
from gevent.server import StreamServer
from gevent.socket import create_connection, gethostbyname


class DoWeirdThingsPlease(StreamServer):

    def __init__(self, listener, dest, config=None, **kwargs):
        StreamServer.__init__(self, listener, **kwargs)
        self.dest = dest
        self.config = config
        self.running = True

    def handle(self, source, address):
        dest = create_connection(self.dest)
        gevent.spawn(self.weirdify, source, dest)
        gevent.spawn(self.weirdify, dest, source)

    def weirdify(self, source, dest):
        try:
            while self.running:
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
