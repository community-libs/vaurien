from abc import ABCMeta, abstractmethod


class Behavior(object):
    """Registry for behaviors.

    A behavior is a class that implements two methods:

    - on_before_handle
    - on_after_handle
    """
    __metaclass__ = ABCMeta
    _cache = {}

    @abstractmethod
    def on_before_handle(self, protocol, source, dest, to_backend):
        pass

    @abstractmethod
    def on_after_handle(self, protocol, source, dest, to_backend):
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
        """Return a mapping of all behaviors.

        The keys are the behavior names and the values the classes.
        """
        return dict([(klass.name, cls._get_instance(klass))
                     for klass in cls._abc_registry])

    @classmethod
    def get_behavior(cls, name):
        for klass in cls._abc_registry:
            if klass.name == name:
                return cls._get_instance(klass)
        raise KeyError(name)


get_behaviors = Behavior.get_behaviors


def get_behavior(name):
    """Returns an instance of the given behavior."""
    return Behavior.get_behaviors(name)()


# manually register built-in behaviors
from vaurien.behaviors.dummy import Dummy
Behavior.register(Dummy)

from vaurien.behaviors.error import Error
Behavior.register(Error)

from vaurien.behaviors.blackout import Blackout
Behavior.register(Blackout)

from vaurien.behaviors.delay import Delay
Behavior.register(Delay)

from vaurien.behaviors.hang import Hang
Behavior.register(Hang)

from vaurien.behaviors.transient import Transient
Behavior.register(Transient)
