from abc import ABCMeta, abstractmethod


class Handler(object):
    __metaclass__ = ABCMeta
    _cache = {}

    @abstractmethod
    def __call__(self, client_sock, backend_sock, to_backend):
        pass

    @classmethod
    def __subclasshook__(cls, klass):
        if cls is Handler:
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
    def get_handlers(cls):
        return dict([(klass.name, cls._get_instance(klass))
                     for klass in cls._abc_registry])

    @classmethod
    def get_handler(cls, name):
        for klass in cls._abc_registry:
            if klass.name == name:
                return cls._get_instance(klass)
        raise KeyError(name)


def get_handlers():
    return Handler.get_handlers()


def get_handler(name):
    return Handler.get_handlers(name)()


# manually register built-in plugins
from vaurien.handlers.dummy import Dummy
Handler.register(Dummy)

from vaurien.handlers.error import Error
Handler.register(Error)

from vaurien.handlers.blackout import Blackout
Handler.register(Blackout)

from vaurien.handlers.delay import Delay
Handler.register(Delay)

from vaurien.handlers.hang import Hang
Handler.register(Hang)
