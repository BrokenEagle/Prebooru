# UTILITY/OBJ.PY

# ## PYTHON IMPORTS
import enum


# ## CLASSES

class classproperty:
    """Decorator for a Class property."""
    def __init__(self, func):
        self.func = func

    def __get__(self, owner_self, owner_cls):
        return self.func(owner_cls)


class memoized_classproperty:
    """Decorator for a Class property with caching."""
    def __init__(self, func):
        self.func = func

    def __get__(self, owner_self, owner_cls):
        keyname = '_' + owner_cls.__name__ + '_' + self.func.__name__
        if not hasattr(owner_cls, keyname):
            val = self.func(owner_cls)
            setattr(owner_cls, keyname, val)
        return getattr(owner_cls, keyname)


class staticproperty:
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

    @classproperty
    def names(cls):
        return [e.name for e in cls]

    @classproperty
    def values(cls):
        return [e.value for e in cls]

    @classmethod
    def by_name(cls, name):
        return cls[name]

    @classmethod
    def by_id(cls, id):
        return cls(id)
