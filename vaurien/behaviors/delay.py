import gevent
from vaurien.behaviors.dummy import Dummy


class Delay(Dummy):
    """Adds a delay before or after the backend is called.

    The delay can happen *after* or *before* the backend is called.
    """
    name = 'delay'
    options = {'sleep': ("Delay in seconds (float)", float, 1),
               'before':
               ("If True adds before the backend is called. Otherwise"
                " after", bool, True)}
    options.update(Dummy.options)

    def on_before_handle(self, protocol, source, dest, to_backend):
        if self.option('before'):
            gevent.sleep(self.option('sleep'))
        return True

    def on_after_handle(self, protocol, source, dest, to_backend):
        if not self.option('before'):
            gevent.sleep(self.option('sleep'))
