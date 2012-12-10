import copy
from vaurien.protocols.tcp import TCP


class MySql(TCP):

    name = 'mysql'
    options = copy.copy(TCP.options)
    del options['keep_alive']

    def update_settings(self, settings):
        if 'keep_alive' in settings:
            del settings['keep_alive']
        super(MySql, self).update_settings(settings)

    def option(self, name):
        if name == 'keep_alive':
            return True
        return super(MySql, self).option(name)
