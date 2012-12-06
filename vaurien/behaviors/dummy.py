

class Dummy(object):
    """Transparent behavior. Nothing's done.
    """
    name = 'dummy'
    options = {}

    def __init__(self):
        self.settings = {}

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

    def on_before_handle(self, protocol, source, dest, to_backend):
        return True

    def on_after_handle(self, protocol, source, dest, to_backend):
        return True
