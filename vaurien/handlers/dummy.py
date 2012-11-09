from gevent.socket import error
from vaurien.handlers.base import BaseHandler


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
               'buffer': ("Buffer size", int, 2048)}

    def __call__(self, client_sock, backend_sock, to_backend):
        data = self._get_data(client_sock, backend_sock, to_backend)
        if data:
            dest = to_backend and backend_sock or client_sock
            source = to_backend and client_sock or backend_sock
            dest.sendall(data)

            # If we are not keeping the connection alive
            # we can suck the answer back and close the socket
            if not self.option('keep_alive'):
                data = ''
                while True:
                    try:
                        data = dest.recv(self.option('buffer'))
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
        elif not to_backend:
            # We want to close the socket if the backend sock is empty
            if not self.option('reuse_socket'):
                backend_sock.close()
                backend_sock._closed = True

        return data != ''
