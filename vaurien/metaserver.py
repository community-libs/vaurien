import sys
import argparse

from gevent.server import StreamServer
from gevent.socket import create_connection, error, gethostbyname

from vaurien.protocols.http import EOH, RE_LEN
from vaurien.behaviors.dummy import Dummy
from vaurien.run import LOG_LEVELS, configure_logger
from vaurien import logger, __version__
from vaurien.util import get_data, chunked


_TMP = """\
HTTP/1.1 %(code)s %(name)s
Content-Type: text/html; charset=UTF-8

<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 3.2 Final//EN">
<title>%(code)s %(name)s</title>
<h1>%(name)s</h1>
%(description)s
"""


def http_error(code='400', name='Bad Request', description='Boo'):
    data = {}
    data['code'] = code
    data['name'] = name
    data['description'] = description
    return _TMP % data


class MetaProxy(StreamServer):
    def __init__(self, host, port):
        self.behavior = Dummy()
        self.behavior_name = 'dummy'
        self.host = gethostbyname(host)
        self.port = port
        location = self.host, self.port
        StreamServer.__init__(self, location)

    def handle(self, client_sock, address):
        client_sock.setblocking(0)
        dest = None
        try:
            # getting the query
            data = get_data(client_sock)

            if not data:
                return

            # finding out what backend we want
            data = data.split('\r\n')

            PATH = data[0].split()
            elmts = PATH[1].split('/')
            try:
                port = int(elmts[1])
            except ValueError:
                client_sock.sendall(http_error(404, 'Not Found'))
                return

            NEW_PATH = '/'.join(elmts[0:1] + elmts[2:])
            data[0] = ' '.join(PATH[0:1] + [NEW_PATH] + PATH[2:])

            try:
                dest = create_connection((self.host, port))
            except error:
                client_sock.sendall(http_error(503, '%d not responding' %
                                    port))
                return

            # sending it to the backend
            dest.sendall('\r\n'.join(data))

            # Receiving the response
            buffer = get_data(dest)

            client_sock.sendall(buffer)

            # Reading the HTTP Headers
            while EOH not in buffer:
                data = get_data(dest)
                buffer += data
                client_sock.sendall(data)

            # content-length header - to see if we need to suck more
            # data.
            match = RE_LEN.search(buffer)
            if match:
                resp_len = int(match.group(1))
                left_to_read = resp_len - len(buffer)
                if left_to_read > 0:
                    for chunk in chunked(left_to_read, 1024):
                        data = get_data(dest, chunk)
                        buffer += data
                        client_sock.sendall(data)
            else:
                # embarrassing...
                # just sucking until recv() returns ''
                while True:
                    data = get_data(dest)
                    if data == '':
                        break
                    client_sock.sendall(data)
        finally:
            client_sock.close()
            if dest is not None:
                dest.close()


def main():
    parser = argparse.ArgumentParser(description='Runs a Meta proxy.')

    # other arguments
    parser.add_argument('--version', action='store_true', default=False,
                        help='Displays version and exits.')
    parser.add_argument('--host', default='localhost',
                        help='Host of the server')
    parser.add_argument('--port', default=9998, type=int,
                        help='Port of the server')

    parser.add_argument('--log-level', dest='loglevel', default='info',
                        choices=LOG_LEVELS.keys() + [key.upper() for key in
                                                     LOG_LEVELS.keys()],
                        help="log level")
    parser.add_argument('--log-output', dest='logoutput', default='-',
                        help="log output")

    # parsing the provided args
    args = parser.parse_args()

    if args.version:
        print(__version__)
        sys.exit(0)

    # configure the logger
    configure_logger(logger, args.loglevel, args.logoutput)
    http_server = MetaProxy(args.host, args.port)

    logger.info('Starting the Meta server: http://%s:%s' %
                (args.host, args.port))

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
    finally:
        logger.info('Bye!')


if __name__ == '__main__':
    main()
