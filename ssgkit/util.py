import os, os.path

def slurp(*path, mode='r'):
    with open(os.path.join(*path), mode) as f:
        return f.read()

def write(path, data, mode='w'):
    # Equivalent to mkdir -p
    os.makedirs(os.path.dirname(path), exist_ok = True)
    with open(path, mode) as f:
        f.write(data)


def lazy(fn):
    '''
    Decorator that makes a property lazy-evaluated.
    See http://stevenloria.com/lazy-evaluated-properties-in-python/
    '''
    attr_name = '_lazy_' + fn.__name__

    def _getter(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)

    def _setter(self, value):
        setattr(self, attr_name, value)

    return property(fget=_getter, fset=_setter)

