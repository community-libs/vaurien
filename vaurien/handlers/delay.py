import gevent
from vaurien.handlers.dummy import Dummy


class Delay(Dummy):
    """Adds a delay before the backend is called.

    The delay can happen *after* or *before* the backend is called.
    """
    name = 'delay'
    options = {'sleep': ("Delay in seconds", int, 1),
               'before':
               ("If True adds before the backend is called. Otherwise"
                " after", bool, True)}
    options.update(Dummy.options)

    def on_before_handler(self):
        if self.option('before'):
            gevent.sleep(self.option('sleep'))

    def on_after_handler(self):
        if not self.option('before'):
            gevent.sleep(self.option('sleep'))
