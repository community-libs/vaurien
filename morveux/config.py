class MorveuxConfig(dict):
    defaults = {
        'sleep_delay': 2,
        'delay_ratio': 10,  # 50%
        'errors_ratio': 5,
        'blackout_ratio': 5,
        'proxy_ratio': 80,
    }

    def __init__(self, **kwargs):
        super(MorveuxConfig, self).__init__(**kwargs)
        for key, value in self.defaults.items():
            self.setdefault(key, value)


class MySQLConfig(MorveuxConfig):
    defaults = {}
