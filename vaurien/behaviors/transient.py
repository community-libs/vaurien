from vaurien.behaviors.error import Error
from vaurien.util import get_data

class Transient(Error):
    name = 'transient'
    options = {'warmup': ("Number of calls before succeeding out", int, 1)}
    options.update(Error.options)

    def __init__(self):
        super(Error, self).__init__()
        self.current = 0

    def on_before_handle(self, protocol, source, dest, to_backend):
        if self.current < self.option('warmup'):
            self.current += 1
            return super(Error, self).on_before_handle(protocol, source,
                                                       dest, to_backend)

        # read the data
        data = get_data(source)
        if not data:
            return False

        if not to_backend:
            # XXX find how to handle errors (which errors should we send)
            # depends on the protocol
            dest.sendall(os.urandom(1000))

        else:          # sending the data tp the backend
            dest.sendall(data)

        return True
