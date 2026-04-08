import abc
import copy
import copyreg
import weakref
from operator import eq
from operator import ge
from operator import gt
from operator import le
from operator import lt
from operator import ne
from test import support

import pytest

from copy import deepcopy

order_comparisons = le, lt, ge, gt
equality_comparisons = eq, ne
comparisons = order_comparisons + equality_comparisons

def test_deepcopy_basic():
    """Modified builtin test.test_copy module,
    pytest code by Arseny Boykov Bobronium@github.com
    """
    x = 42
    y = deepcopy(x)
    assert y == x


def test_deepcopy_same_object():
    """Previously was called test_deepcopy_memo, but I find new name to be clearer
    Tests of reflexive objects are under type-specific sections below.
    This tests only repetitions of objects.
    """
    x = []
    x = [x, x]
    y = deepcopy(x)
    assert y == x
    assert y is not x
    assert y[0] is not x[0]
    assert y[0] is y[1]


def test_deepcopy_issubclass():
    """N.B. there's no way to test the TypeError coming out of
    issubclass() -- this can only happen when an extension
    module defines a "type" that doesn't formally inherit from
    type.
    """
    class Meta(type):
        pass

    class C(metaclass=Meta):
        pass

    assert deepcopy(C) == C


def test_deepcopy_deepcopy():
    class C(object):
        def __init__(self, foo):
            self.foo = foo

        def __deepcopy__(self, memo=None):
            return C(self.foo)

    x = C(42)
    y = deepcopy(x)
    assert y.__class__ == x.__class__
    assert y.foo == x.foo


def test_deepcopy_registry():
    class C(object):
        def __new__(cls, foo):
            obj = object.__new__(cls)
            obj.foo = foo
            return obj

    def pickle_C(obj):
        return (C, (obj.foo,))

    x = C(42)
    with pytest.raises(TypeError):
        deepcopy(x)
    copyreg.pickle(C, pickle_C, C)
    deepcopy(x)


def test_deepcopy_reduce_ex():
    class C(object):
        def __reduce_ex__(self, proto):
            c.append(1)
            return ""

        def __reduce__(self):
            self.fail("shouldn't call this")

    c = []
    x = C()
    y = deepcopy(x)
    assert y is x
    assert c == [1]


def test_deepcopy_reduce():
    class C(object):
        def __reduce__(self):
            c.append(1)
            return ""

    c = []
    x = C()
    y = deepcopy(x)
    assert y is x
    assert c == [1]


def test_deepcopy_cant():
    class C(object):
        def __getattribute__(self, name):
            if name.startswith("__reduce"):
                raise AttributeError(name)
            return object.__getattribute__(self, name)

    x = C()


# Type-specific _deepcopy_xxx() functions.


def get_deepcopy_atomic():
    class Classic:
        pass

    class NewStyle(object):
        pass

    def f():
        pass

    return [
        None,
        42,
        2**100,
        3.14,
        True,
        False,
        1j,
        "hello",
        "hello\u1234",
        f.__code__,
        NewStyle,
        range(10),
        Classic,
        max,
        property(),
    ]


@pytest.mark.parametrize("x", get_deepcopy_atomic())
def test_deepcopy_atomic(x):
    assert deepcopy(x) is x


def test_deepcopy_list():
    x = [[1, 2], 3]
    y = deepcopy(x)
    assert y == x
    assert x is not y
    assert x[0] is not y[0]


@pytest.mark.parametrize("op", comparisons)
def test_deepcopy_reflexive_list(op):
    x = []
    x.append(x)
    y = deepcopy(x)
    with pytest.raises(RecursionError):
        op(y, x)
    assert y is not x
    assert y[0] is y
    assert len(y) == 1


def test_deepcopy_empty_tuple():
    x = ()
    y = deepcopy(x)
    assert x is y


def test_deepcopy_tuple():
    x = ([1, 2], 3)
    y = deepcopy(x)
    assert y == x
    assert x is not y
    assert x[0] is not y[0]


def test_deepcopy_tuple_of_immutables():
    x = ((1, 2), 3)
    y = deepcopy(x)
    assert x is y


@pytest.mark.parametrize("op", comparisons)
def test_deepcopy_reflexive_tuple(op):
    x = ([], 4, 3)
    x[0].append(x)
    y = deepcopy(x)
    assert y is not x
    assert y[0] is not x[0]
    assert y[0][0] is y

    with pytest.raises(RecursionError):
        op(y, x)


def test_deepcopy_dict():
    x = {"foo": [1, 2], "bar": 3}
    y = deepcopy(x)
    assert y == x
    assert x is not y
    assert x["foo"] is not y["foo"]


@pytest.mark.parametrize("order_op,eq_op", zip(order_comparisons, equality_comparisons))
def test_deepcopy_reflexive_dict_order(order_op, eq_op):
    x = {}
    x["foo"] = x
    y = deepcopy(x)
    with pytest.raises(TypeError):
        order_op(y, x)
    with pytest.raises(RecursionError):
        eq_op(y, x)
    assert y is not x
    assert y["foo"] is y
    assert len(y) == 1

def test_deepcopy_keepalive():
    memo = {}
    x = []
    deepcopy(x, memo)
    assert memo[id(memo)][0] is x

def test_deepcopy_dont_memo_immutable():
    memo = {}
    x = [1, 2, 3, 4]
    y = deepcopy(x, memo)
    assert y == x
    # There's the entry for the new list, and the keep alive.
    assert len(memo) == 2

    memo = {}
    x = [(1, 2)]
    y = deepcopy(x, memo)
    assert y == x
    # Tuples with immutable contents are immutable for deepcopy.
    assert len(memo) == 2


def test_deepcopy_inst_vanilla():
    class C:
        def __init__(self, foo):
            self.foo = foo

        def __eq__(self, other):
            return self.foo == other.foo

    x = C([42])
    y = deepcopy(x)
    assert y == x
    assert y.foo is not x.foo


def test_deepcopy_inst_deepcopy():
    class C:
        def __init__(self, foo):
            self.foo = foo

        def __deepcopy__(self, memo):
            return C(deepcopy(self.foo, memo))

        def __eq__(self, other):
            return self.foo == other.foo

    x = C([42])
    y = deepcopy(x)
    assert y == x
    assert y is not x
    assert y.foo is not x.foo


def test_deepcopy_inst_getinitargs():
    class C:
        def __init__(self, foo):
            self.foo = foo

        def __getinitargs__(self):
            return (self.foo,)

        def __eq__(self, other):
            return self.foo == other.foo

    x = C([42])
    y = deepcopy(x)
    assert y == x
    assert y is not x
    assert y.foo is not x.foo


def test_deepcopy_inst_getnewargs():
    class C(int):
        def __new__(cls, foo):
            self = int.__new__(cls)
            self.foo = foo
            return self

        def __getnewargs__(self):
            return (self.foo,)

        def __eq__(self, other):
            return self.foo == other.foo

    x = C([42])
    y = deepcopy(x)
    assert isinstance(y, C)
    assert y == x
    assert y is not x
    assert y.foo == x.foo
    assert y.foo is not x.foo


def test_deepcopy_inst_getnewargs_ex():
    class C(int):
        def __new__(cls, *, foo):
            self = int.__new__(cls)
            self.foo = foo
            return self

        def __getnewargs_ex__(self):
            return (), {"foo": self.foo}

        def __eq__(self, other):
            return self.foo == other.foo

    x = C(foo=[42])
    y = deepcopy(x)
    assert isinstance(y, C)
    assert y == x
    assert y is not x
    assert y.foo == x.foo
    assert y.foo is not x.foo


def test_deepcopy_inst_getstate():
    class C:
        def __init__(self, foo):
            self.foo = foo

        def __getstate__(self):
            return {"foo": self.foo}

        def __eq__(self, other):
            return self.foo == other.foo

    x = C([42])
    y = deepcopy(x)
    assert y == x
    assert y is not x
    assert y.foo is not x.foo


def test_deepcopy_inst_setstate():
    class C:
        def __init__(self, foo):
            self.foo = foo

        def __setstate__(self, state):
            self.foo = state["foo"]

        def __eq__(self, other):
            return self.foo == other.foo

    x = C([42])
    y = deepcopy(x)
    assert y == x
    assert y is not x
    assert y.foo is not x.foo


def test_deepcopy_inst_getstate_setstate():
    class C:
        def __init__(self, foo):
            self.foo = foo

        def __getstate__(self):
            return self.foo

        def __setstate__(self, state):
            self.foo = state

        def __eq__(self, other):
            return self.foo == other.foo

    x = C([42])
    y = deepcopy(x)
    assert y == x
    assert y is not x
    assert y.foo is not x.foo
    # State with boolean value is false (issue #25718).
    x = C([])
    y = deepcopy(x)
    assert y == x
    assert y is not x
    assert y.foo is not x.foo


def test_deepcopy_reflexive_inst():
    class C:
        pass

    x = C()
    x.foo = x
    y = deepcopy(x)
    assert y is not x
    assert y.foo is y


# _reconstruct()


def test_reconstruct_string():
    class C(object):
        def __reduce__(self):
            return ""

    x = C()
    y = copy.copy(x)
    assert y is x
    y = deepcopy(x)
    assert y is x


def test_reconstruct_nostate():
    class C(object):
        def __reduce__(self):
            return (C, ())

    x = C()
    x.foo = 42
    y = copy.copy(x)
    assert y.__class__ is x.__class__
    y = deepcopy(x)
    assert y.__class__ is x.__class__


def test_reconstruct_state():
    class C(object):
        def __reduce__(self):
            return (C, (), self.__dict__)

        def __eq__(self, other):
            return self.__dict__ == other.__dict__

    x = C()
    x.foo = [42]
    y = copy.copy(x)
    assert y == x
    y = deepcopy(x)
    assert y == x
    assert y.foo is not x.foo


def test_reconstruct_state_setstate():
    class C(object):
        def __reduce__(self):
            return (C, (), self.__dict__)

        def __setstate__(self, state):
            self.__dict__.update(state)

        def __eq__(self, other):
            return self.__dict__ == other.__dict__

    x = C()
    x.foo = [42]
    y = copy.copy(x)
    assert y == x
    y = deepcopy(x)
    assert y == x
    assert y.foo is not x.foo


def test_reconstruct_reflexive():
    class C(object):
        pass

    x = C()
    x.foo = x
    y = deepcopy(x)
    assert y is not x
    assert y.foo is y


# Additions for Python 2.3 and pickle protocol 2.


def test_reduce_4tuple():
    class C(list):
        def __reduce__(self):
            return (C, (), self.__dict__, iter(self))

        def __eq__(self, other):
            return list(self) == list(other) and self.__dict__ == other.__dict__

    x = C([[1, 2], 3])
    y = copy.copy(x)
    assert x == y
    assert x is not y
    assert x[0] is y[0]
    y = deepcopy(x)
    assert x == y
    assert x is not y
    assert x[0] is not y[0]


def test_reduce_5tuple():
    class C(dict):
        def __reduce__(self):
            return (C, (), self.__dict__, None, self.items())

        def __eq__(self, other):
            return dict(self) == dict(other) and self.__dict__ == other.__dict__

    x = C([("foo", [1, 2]), ("bar", 3)])
    y = copy.copy(x)
    assert x == y
    assert x is not y
    assert x["foo"] is y["foo"]
    y = deepcopy(x)
    assert x == y
    assert x is not y
    assert x["foo"] is not y["foo"]


def test_deepcopy_slots():
    class C(object):
        __slots__ = ["foo"]

    x = C()
    x.foo = [42]
    y = deepcopy(x)
    assert x.foo == y.foo
    assert x.foo is not y.foo


def test_deepcopy_dict_subclass():
    class C(dict):
        def __init__(self, d=None):
            if not d:
                d = {}
            self._keys = list(d.keys())
            super().__init__(d)

        def __setitem__(self, key, item):
            super().__setitem__(key, item)
            if key not in self._keys:
                self._keys.append(key)

    x = C(d={"foo": 0})
    y = deepcopy(x)
    assert x == y
    assert x._keys == y._keys
    assert x is not y
    x["bar"] = 1
    assert x != y
    assert x._keys != y._keys


def test_deepcopy_list_subclass():
    class C(list):
        pass

    x = C([[1, 2], 3])
    x.foo = [4, 5]
    y = deepcopy(x)
    assert list(x) == list(y)
    assert x.foo == y.foo
    assert x[0] is not y[0]
    assert x.foo is not y.foo


def test_deepcopy_tuple_subclass():
    class C(tuple):
        pass

    x = C([[1, 2], 3])
    assert tuple(x) == ([1, 2], 3)
    y = deepcopy(x)
    assert tuple(y) == ([1, 2], 3)
    assert x is not y
    assert x[0] is not y[0]


def test_deepcopy_function():
    assert deepcopy(global_foo) == global_foo

    def foo(x, y):
        return x + y

    assert deepcopy(foo) == foo

    def bar():
        return None

    assert deepcopy(bar) == bar


def check_weakref(_copy):
    class C(object):
        pass

    obj = C()
    x = weakref.ref(obj)
    y = _copy(x)
    assert y is x
    del obj
    y = _copy(x)
    assert y is x


def test_deepcopy_weakref():
    check_weakref(deepcopy)


def check_copy_weakdict(_dicttype):
    class C(object):
        pass

    a, b, c, d = [C() for i in range(4)]
    u = _dicttype()
    u[a] = b
    u[c] = d
    v = copy.copy(u)
    assert v is not u
    assert v == u
    assert v[a] == b
    assert v[c] == d
    assert len(v) == 2
    del c, d
    support.gc_collect()  # For PyPy or other GCs.
    assert len(v) == 1
    x, y = C(), C()
    # The underlying containers are decoupled.
    v[x] = y
    assert x not in u


def test_copy_weakkeydict():
    check_copy_weakdict(weakref.WeakKeyDictionary)


def test_copy_weakvaluedict():
    check_copy_weakdict(weakref.WeakValueDictionary)


def test_deepcopy_weakkeydict():
    class C(object):
        def __init__(self, i):
            self.i = i

    a, b, c, d = [C(i) for i in range(4)]
    u = weakref.WeakKeyDictionary()
    u[a] = b
    u[c] = d
    # Keys aren't copied, values are.
    v = deepcopy(u)
    assert v != u
    assert len(v) == 2
    assert v[a] is not b
    assert v[c] is not d
    assert v[a].i == b.i
    assert v[c].i == d.i
    del c
    support.gc_collect()  # For PyPy or other GCs.
    assert len(v) == 1


def test_deepcopy_weakvaluedict():
    class C(object):
        def __init__(self, i):
            self.i = i

    a, b, c, d = [C(i) for i in range(4)]
    u = weakref.WeakValueDictionary()
    u[a] = b
    u[c] = d
    # Keys are copied, values aren't.
    v = deepcopy(u)
    assert v != u
    assert len(v) == 2
    (x, y), (z, t) = sorted(v.items(), key=lambda pair: pair[0].i)
    assert x is not a
    assert x.i == a.i
    assert y is b
    assert z is not c
    assert z.i == c.i
    assert t is d
    del x, y, z, t
    del d
    support.gc_collect()  # For PyPy or other GCs.
    assert len(v) == 1


def test_deepcopy_bound_method():
    class Foo(object):
        def m(self):
            pass

    f = Foo()
    f.b = f.m
    g = deepcopy(f)
    assert g.m == g.b
    assert g.b.__self__ is g
    g.b()


def global_foo(x, y):
    return x + y
