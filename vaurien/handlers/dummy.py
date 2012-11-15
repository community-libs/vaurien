import re
from vaurien.handlers.base import BaseHandler


RE_LEN = re.compile('Content-Length: (\d+)', re.M | re.I)
RE_KEEPALIVE = re.compile('Connection: Keep-Alive')
RE_MEMCACHE_COMMAND = re.compile('(.*)\r\n')

EOH = '\r\n\r\n'
CRLF = '\r\n'


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


_PROTOCOLS = ['tcp', 'redis', 'memache', 'http']


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
               'protocol': ("Protocol used", str, 'tcp', _PROTOCOLS)}

    #
    # Events
    #
    def on_before_handler(self):
        pass

    def on_after_handler(self):
        pass

    def _abandon(self, to_backend, backend_sock):
        if not to_backend:
            # We want to close the socket if the backend sock is empty
            if not self.option('reuse_socket'):
                backend_sock.close()
                backend_sock._closed = True

    def _redis(self, source, dest, to_backend):
        """ see http://redis.io/topics/protocol
        """
        # Getting the request.
        buffer = self._get_data(source)
        if not buffer:
            self._abandon(to_backend, dest)
            return

        # Sending the request to the backend.
        self.on_before_send_data(source, dest)
        dest.sendall(buffer)

        # Getting the answer back and sending it over.
        buffer_size = self.option('buffer')
        buffer = dest.recv(buffer_size)
        source.sendall(buffer)
        already_read = len(buffer)

        if buffer[0] in ('+', '-', ':'):
            # simple reply, we're good
            return False    # disconnect mode ?

        if buffer[0] == '$':
            # bulk reply
            size = int(buffer[1:buffer.find(CRLF)])
            left_to_read = size - already_read

            if left_to_read > 0:
                for chunk in chunked(left_to_read, buffer_size):
                    data = source.recv(chunk)
                    buffer += data
                    dest.sendall(data)

            return False  # disconnect mode ?

        if buffer[0] == '*':
            # multi-bulk reply
            raise NotImplementedError()

        raise NotImplementedError()

    def _memcache(self, source, dest, to_backend):
        # https://github.com/memcached/memcached/blob/master/doc/protocol.txt

        # Sending the query
        buffer = self._get_data(source)
        if not buffer:
            self._abandon(to_backend, dest)
            return

        # sending the first packet
        dest.sendall(buffer)

        # finding the command we sent.
        cmd = RE_MEMCACHE_COMMAND.search(buffer)

        if cmd is None:
            # wat ?
            self._abandon(to_backend, dest)
            return

        # looking at the command
        cmd = cmd.groups()[0]
        buffer_size = self.option('buffer')

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

    def _http(self, source, dest, to_backend):
        buffer_size = self.option('buffer')

        # Getting the HTTP query
        data = self._get_data(source)

        if not data:
            self._abandon(to_backend, dest)
            return

        # sending it to the backend
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

        # content-length header - to see if we need to suck more
        # data.
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
            source.close()
            source._closed = True

        if not self.option('reuse_socket') and not self.option('keep_alive'):
            dest.close()
            dest._closed = True

        # we're done
        return keep_alive or self.option('keep_alive')

    def _tcp(self, source, dest, to_backend):
        # default TCP behavior
        data = self._get_data(source)
        if data:
            dest.sendall(data)

            # If we are not keeping the connection alive
            # we can suck the answer back and close the socket
            if not self.option('keep_alive'):
                # just suck it until it's empty
                data = ''
                while True:
                    data = self._get_data(dest)
                    if data == '':
                        break
                    source.sendall(data)

                if not self.option('reuse_socket'):
                    dest.close()
                    dest._closed = True

                # we're done - False means we'll disconnect the client
                return False
        else:
            self._abandon(to_backend, dest)

        return data != ''

    def __call__(self, source, dest, to_backend):
        self.on_before_handler()

        try:
            # specific protocol implementations
            if self.option('protocol') == 'http':
                return self._http(source, dest, to_backend)
            elif self.option('protocol') == 'memcache':
                return self._memcache(source, dest, to_backend)
            elif self.option('protocol') == 'redis':
                return self._redis(source, dest, to_backend)

            return self._tcp(source, dest, to_backend)
        finally:
            self.on_after_handler()
