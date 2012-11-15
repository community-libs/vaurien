from abc import ABCMeta, abstractmethod


class Behavior(object):
    __metaclass__ = ABCMeta
    _cache = {}

    @abstractmethod
    def __call__(self, client_sock, backend_sock, to_backend):
        pass

    @classmethod
    def __subclasshook__(cls, klass):
        if cls is Behavior:
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
    def get_behaviors(cls):
        return dict([(klass.name, cls._get_instance(klass))
                     for klass in cls._abc_registry])

    @classmethod
    def get_behavior(cls, name):
        for klass in cls._abc_registry:
            if klass.name == name:
                return cls._get_instance(klass)
        raise KeyError(name)


def get_behaviors():
    return Behavior.get_behaviors()


def get_behavior(name):
    return Behavior.get_behaviors(name)()


# manually register built-in plugins
from vaurien.behaviors.dummy import Dummy
Behavior.register(Dummy)

#from vaurien.behaviors.error import Error
#Behavior.register(Error)

#from vaurien.behaviors.blackout import Blackout
#Behavior.register(Blackout)

#from vaurien.behaviors.delay import Delay
#Behavior.register(Delay)

#from vaurien.behaviors.hang import Hang
#Behavior.register(Hang)
