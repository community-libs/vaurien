import copy
from vaurien.util import get_data


class BaseProtocol(object):

    name = ''
    options = {'reuse_socket': ("If True, the socket is reused.",
                                bool, False),
               'buffer': ("Buffer size", int, 8124),
               'keep_alive': ("Keep the connection alive", bool, False)
               }

    def __init__(self, settings=None, proxy=None):
        self.proxy = proxy
        if proxy is not None:
            self.logger = self.proxy._logger
        else:
            self.logger = None

        if settings is None:
            self.settings = {}
        else:
            self.settings = copy.copy(settings)

    def _abort_handling(self, to_backend, backend_sock):
        if not to_backend:
            # We want to close the socket if the backend sock is empty
            if not self.option('reuse_socket'):
                backend_sock.close()
                backend_sock._closed = True

    def update_settings(self, settings):
        self.settings.update(settings)

    def _convert(self, value, type_):
        if isinstance(value, type_):
            return value
        if type_ == bool:
            value = value.lower()
            return value in ('y', 'yes', '1', 'on')
        return type_(value)

    def option(self, name):
        type_, default = self.options[name][1:3]
        value = self.settings.get(name, default)
        return self._convert(value, type_)

    def _get_data(self, sock, buffer=None):
        if buffer is None:
            buffer = self.option('buffer')
        return get_data(sock, buffer)

    def __call__(self, source, dest, to_backend, behavior):
        if not behavior.on_before_handle(self, source, dest, to_backend):
            return True
        try:
            return self._handle(source, dest, to_backend)
        finally:
            behavior.on_after_handle(self, source, dest, to_backend)
