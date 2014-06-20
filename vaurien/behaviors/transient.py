from vaurien.behaviors.error import Error
from vaurien.util import get_data

class Transient(Error):
    name = 'transient'
    options = {'agitate': ("Number of calls before succeeding", int, 1)}
    options.update(Error.options)

    def __init__(self):
        super(Transient, self).__init__()
        self.current = 0

    def on_before_handle(self, protocol, source, dest, to_backend):
        if self.current < self.option('agitate'):
            self.current += 1
            return super(Transient, self).on_before_handle(protocol, source,
                                                       dest, to_backend)

        return True
