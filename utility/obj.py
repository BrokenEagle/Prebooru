# UTILITY/OBJ.PY

# ## PYTHON IMPORTS
import enum


# ## FUNCTIONS

def classproperty(cached=False):
    def _decorator(function):
        return CacheClassProperty(function, cached)
    return _decorator


# ## CLASSES

class CacheClassProperty:
    """Decorator for a Class property with optional caching.
       Must be used with classproperty if the cached is used.
    """
    def __init__(self, func, cached=False):
        self.func = func
        self.cached = cached

    def __get__(self, owner_self, owner_cls):
        if self.cached:
            keyname = '_' + owner_cls.__name__ + '_' + self.func.__name__
            if not hasattr(owner_cls, keyname):
                val = self.func(owner_cls)
                setattr(owner_cls, keyname, val)
            return getattr(owner_cls, keyname)
        else:
            return self.func(owner_cls)


class StaticProperty:
    """Decorator for a static property.
    """
    def __init__(self, fget=None, fset=None, fdel=None):
        self.fget = fget
        self.fset = fset
        self.fdel = fdel

    def setter(self, fset):
        self.fset = fset
        return self

    def deleter(self, fdel):
        self.fdel = fdel
        return self

    def __get__(self, instance, owner=None):
        return self.fget()

    def __set__(self, instance, value):
        return self.fset(value)

    def __delete__(self, instance):
        return self.fdel()


class AttrEnum(enum.IntEnum):
    @property
    def id(self):
        return self.value

    @classproperty(cached=False)
    def names(cls):
        return [e.name for e in cls]

    @classproperty(cached=False)
    def values(cls):
        return [e.value for e in cls]

    @classmethod
    def by_name(cls, name):
        return cls[name]

    @classmethod
    def by_id(cls, id):
        return cls(id)
