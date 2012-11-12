import re

from gevent.socket import error
from vaurien.handlers.base import BaseHandler


RE_LEN = re.compile('Content-Length: (\d+)', re.M | re.I)


def chunked(total, chunk):
    if total <= chunk:
        yield total
    else:
        data = total
        while data > 0:
            yield chunk
            if data < chunk:
                chunk = data
            else:
                data -= chunk


class Dummy(BaseHandler):
    """Dummy handler.

    Every incoming data is passed to the backend with no alteration,
    and vice-versa.
    """
    name = 'dummy'
    options = {'keep_alive': ("Keep-alive protocol",
                              bool, False),
               'reuse_socket': ("If True, the socket is reused.",
                                bool, False),
               'buffer': ("Buffer size", int, 2048),
               'protocol': ("Protocol used", str, 'unknown')}

    def __call__(self, client_sock, backend_sock, to_backend):
        data = self._get_data(client_sock, backend_sock, to_backend)
        if data:
            dest = to_backend and backend_sock or client_sock
            source = to_backend and client_sock or backend_sock
            dest.sendall(data)

            # If we are not keeping the connection alive
            # we can suck the answer back and close the socket
            if not self.option('keep_alive'):
                http = self.option('protocol') == 'http'
                buffer_size = self.option('buffer')

                # If we are handling HTTP we need to get the headers
                # and determinate the size of the response, then
                # suck the rest of the response.
                #
                # (and send stuff back to the client in the meantime)
                #

                # XXX extra work here, but the basis for other handlers
                if http:
                    end_of_header = '\r\n\r\n'

                    buffer = dest.recv(buffer_size)
                    source.sendall(buffer)

                    while end_of_header not in buffer:
                        data = dest.recv(buffer_size)
                        buffer += data
                        source.sendall(data)

                    # let's find out the length
                    # and read the rest
                    match = RE_LEN.search(buffer)
                    if match:
                        resp_len = int(match.group(1))
                        left_to_read = resp_len - len(buffer)
                        if left_to_read > 0:
                            for chunk in chunked(left_to_read, buffer_size):
                                data = dest.recv(chunk)
                                buffer += data
                                source.sendall(data)
                else:
                    # just suck it until it's empty
                    data = ''
                    while True:
                        try:
                            data = dest.recv(buffer_size)
                        except error, err:
                            if err.errno == 35:
                                continue

                        if data == '':
                            break
                        source.sendall(data)

                dest.close()
                dest._closed = True

                if not self.option('reuse_socket'):
                    backend_sock.close()
                    backend_sock._closed = True

                # we're done
                return False
        elif not to_backend:
            # We want to close the socket if the backend sock is empty
            if not self.option('reuse_socket'):
                backend_sock.close()
                backend_sock._closed = True

        return data != ''
