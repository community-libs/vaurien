import re

from gevent.socket import error
from vaurien.handlers.base import BaseHandler


RE_LEN = re.compile('Content-Length: (\d+)', re.M | re.I)
RE_KEEPALIVE = re.compile('Connection: Keep-Alive')
RE_MEMCACHE_COMMAND = re.compile('(.*)\r\n')

EOH = '\r\n\r\n'


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
    options = {'keep_alive': ("Keep-alive protocol (auto-detected with http)",
                              bool, False),
               'reuse_socket': ("If True, the socket is reused.",
                                bool, False),
               'buffer': ("Buffer size", int, 2048),
               'protocol': ("Protocol used", str, 'unknown')}

    def _memcache(self, client_sock, backend_sock, to_backend):
        buffer_size = self.option('buffer')

        # Sending the query
        buffer = self._get_data(client_sock, backend_sock, to_backend)
        if not buffer:
            if not to_backend:
                # We want to close the socket if the backend sock is empty
                if not self.option('reuse_socket'):
                    backend_sock.close()
                    backend_sock._closed = True
            return

        # sending the first packet
        dest = to_backend and backend_sock or client_sock
        source = to_backend and client_sock or backend_sock
        dest.sendall(buffer)

        # finding the command sent.
        cmd = RE_MEMCACHE_COMMAND.search(buffer)

        if cmd is None:
            # wat ?
            if not to_backend:
                # We want to close the socket if the backend sock is empty
                if not self.option('reuse_socket'):
                    backend_sock.close()
                    backend_sock._closed = True
            return

        # looking at the command
        cmd = cmd.groups()[0]

        if cmd in ('set', 'add', 'replace', 'append'):
            cmd_size = len(cmd) + len('\r\n')
            data_size = int(cmd.split()[-1])
            total_size = cmd_size + data_size

            # grabbing more data if needed
            left_to_read = total_size - len(buffer)
            if left_to_read > 0:
                for chunk in chunked(left_to_read, buffer_size):
                    data = source.recv(chunk)
                    buffer += data
                    dest.sendall(data)

        # Receiving the response now
        buffer = dest.recv(buffer_size)
        source.sendall(buffer)

        if buffer.startswith('VALUE'):
            # we're getting back a value.
            EOW = 'END\r\n'
        else:
            EOW = '\r\n'

        while not buffer.endswith(EOW):
            data = dest.recv(buffer_size)
            buffer += data
            source.sendall(data)

        # we're done
        return True    # keeping connected

    def _http(self, client_sock, backend_sock, to_backend):
        buffer_size = self.option('buffer')

        # Sending the query
        data = self._get_data(client_sock, backend_sock, to_backend)
        if not data:
            if not to_backend:
                # We want to close the socket if the backend sock is empty
                if not self.option('reuse_socket'):
                    backend_sock.close()
                    backend_sock._closed = True
            return

        dest = to_backend and backend_sock or client_sock
        source = to_backend and client_sock or backend_sock
        dest.sendall(data)

        # Receiving the response
        buffer = dest.recv(buffer_size)
        source.sendall(buffer)

        # Reading the HTTP Headers
        while EOH not in buffer:
            data = dest.recv(buffer_size)
            buffer += data
            source.sendall(data)

        # keep alive header ?
        keep_alive = RE_KEEPALIVE.search(buffer) is not None

        # content-length header
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
            # embarrassing...
            # just sucking until recv() returns ''
            while True:
                data = dest.recv(buffer_size)
                if data == '':
                    break
                source.sendall(data)

        # do we close the client ?
        if not keep_alive and not self.option('keep_alive'):
            dest.close()
            dest._closed = True

        if not self.option('reuse_socket') and not self.option('keep_alive'):
            backend_sock.close()
            backend_sock._closed = True

        # we're done
        return keep_alive or self.option('keep_alive')

    def __call__(self, client_sock, backend_sock, to_backend):
        if self.option('protocol') == 'http':
            return self._http(client_sock, backend_sock, to_backend)
        elif self.option('protocol') == 'memcache':
            return self._memcache(client_sock, backend_sock, to_backend)

        data = self._get_data(client_sock, backend_sock, to_backend)
        if data:
            dest = to_backend and backend_sock or client_sock
            source = to_backend and client_sock or backend_sock
            dest.sendall(data)

            # If we are not keeping the connection alive
            # we can suck the answer back and close the socket
            if not self.option('keep_alive'):
                buffer_size = self.option('buffer')
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
