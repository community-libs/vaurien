import logging

__version__ = '0.1'
logger = logging.getLogger('vaurien')

# shortcuts
from vaurien.client import Client                   # NOQA
from vaurien.util import start_proxy, stop_proxy    # NOQA
