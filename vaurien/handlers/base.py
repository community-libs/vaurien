import copy
from gevent.socket import error


class BaseHandler(object):

    options = {}
    name = ''

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

    def _get_data(self, sock, buffer=1024):
        try:
            data = sock.recv(self.option('buffer'))
        except error:   # for the async mode
            # XXX on 35 we should retry
            data = ''

        return data
