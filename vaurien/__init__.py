import logging

__version__ = '1.9'
logger = logging.getLogger('vaurien')

# shortcuts
try:
    from vaurien.client import Client                   # NOQA
    from vaurien.util import start_proxy, stop_proxy    # NOQA
except ImportError:
    # that may be at installation time
    Client = start_proxy = stop_proxy = None            # NOQA
