from abc import ABCMeta, abstractmethod


class Protocol(object):
    """Registry for protocol.

    A protocol is a class that implements a __call__ method.
    """

    __metaclass__ = ABCMeta
    _cache = {}

    @abstractmethod
    def __call__(self, client_sock, backend_sock, to_backend):
        pass

    @classmethod
    def __subclasshook__(cls, klass):
        if cls is Protocol:
            for method in cls.__abstractmethods__:
                if any(method in base.__dict__ for base in klass.__mro__):
                    continue
                return NotImplemented
            return True
        return NotImplemented

    @classmethod
    def register(cls, subclass):
        ABCMeta.register(cls, subclass)
        if subclass not in cls._abc_registry:
            cls._abc_registry.add(subclass)

    @classmethod
    def _get_instance(cls, klass):
        name = klass.name
        if name not in cls._cache:
            cls._cache[name] = klass()
        return cls._cache[name]

    @classmethod
    def get_protocols(cls):
        """Return a mapping of all protocols.

        The keys are the protocol names and the values the classes.
        """
        return dict([(klass.name, cls._get_instance(klass))
                     for klass in cls._abc_registry])

    @classmethod
    def get_protocol(cls, name):
        for klass in cls._abc_registry:
            if klass.name == name:
                return cls._get_instance(klass)
        raise KeyError(name)


get_protocols = Protocol.get_protocols


def get_protocol(name):
    """Returns an instance of the given protocol."""
    return Protocol.get_protocol(name)()


# manually register built-in protocols
from vaurien.protocols.tcp import TCP
Protocol.register(TCP)

from vaurien.protocols.redis import Redis
Protocol.register(Redis)

from vaurien.protocols.memcache import Memcache
Protocol.register(Memcache)

from vaurien.protocols.http import Http
Protocol.register(Http)

from vaurien.protocols.smtp import SMTP
Protocol.register(SMTP)

from vaurien.protocols.mysql import MySql
Protocol.register(MySql)
