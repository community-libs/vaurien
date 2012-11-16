from vaurien.protocols.tcp import TCP


class SMTP(TCP):
    """SMTP Handler

    """
    name = 'smtp'
    options = TCP.options

    # forcing keep-alive to True
    options['keep_alive'] = (options['keep_alive'][0],
                             options['keep_alive'][1],
                             True)

    def update_settings(self, settings):
        if 'keep_alive' in settings:
            del settings['keep_alive']
        super(SMTP, self).update_settings(settings)
