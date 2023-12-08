#!/usr/bin/env python3

import inspect
import json
import time
import textwrap
from contextlib import contextmanager

import astrocache
import foo


def announce(msg):
    print()
    print('#' * (len(msg) + 4))
    print('# ' + msg + ' #')
    print('#' * (len(msg) + 4))


def test(fn, *args, **kwargs):
    param_str = ', '.join([*map(repr, sanitize(args)),
                           *[f"{k}={v}" for k,v in sanitize(kwargs).items()]])
    try:
        result = fn(*args, **kwargs)
    except Exception as e:
        result = f"{type(e).__name__}: {e}"
    if hasattr(fn, '__self__'):
        owner = fn.__self__
        if hasattr(owner, '__name__'):
            owner_name = owner.__name__
        else:
            owner_name = str(owner)
        name = f"{owner_name}.{fn.__name__}"
    else:
        name = fn.__qualname__
    print(f"{name}({param_str}) => {result}")


@contextmanager
def catch_exception():
    try:
        yield
    except Exception as e:
        print(f"Exception: {e}")


def func_fingerprint_hash(func, **kwargs):
    return astrocache._make_hash(astrocache._func_fingerprint(one, **kwargs))


def print_fingerprint(func):
    print(f"Fingerprint hash for {func.__name__}(): {func_fingerprint_hash(func)}")


def two(c):
    # Call a function in a different module
    return foo.three({'a': c + 1})


def make_thing(a):
    return a + 1


def nested_function_def():
    def blah(x):
        return x + 1


def nested_class_def():
    class Foo:
        def __init__(self, a):
            self.thing = make_thing(a)
    return Foo


def fn_to_assign(x):
    return x + 1


def fn_to_pass(x):
    return x * 1


def think_about_function(fn):
    thoughts = [fn]
    return fn


def one(a, b):
    # Call a function that contains a function definition
    nested_function_def()
    # Call a function that contains a class definition
    nested_class_def()
    # Assign a function to a variable, but don't call it
    fn = fn_to_assign
    # Pass a function as an argument, but don't call it
    think_about_function(fn_to_pass)
    return two(a + b)


announce("function implementation fingerprint")

print("Using the following definitions:")
print(inspect.getsource(foo.three))
print(inspect.getsource(two))
print(inspect.getsource(make_thing))
print(inspect.getsource(nested_function_def))
print(inspect.getsource(nested_class_def))
print(inspect.getsource(fn_to_assign))
print(inspect.getsource(fn_to_pass))
print(inspect.getsource(one))

print_fingerprint(one)

print("\nAdding a comment to make_thing()")
def make_thing(a):
    # comment
    return a + 1

print_fingerprint(one)

print("\nChanging some formatting in make_thing()")
def make_thing(a):
    # comment

    return (a + \
            1)

print_fingerprint(one)

print("\nChanging implementation of make_thing()")
# Lineage: one() -> nested_function_def() -> class Foo -> __init__ -> make_thing()
def make_thing(a):
    return a + 2

print_fingerprint(one)

print("\nChanging implementation of fn_to_assign()")
# TODO: support this! fingerprint should change
def fn_to_assign(x):
    return x + 2

print_fingerprint(one)

print("\nChanging implementation of fn_to_pass()")
# TODO: support this! fingerprint should change
def fn_to_pass(x):
    return x * 2

print_fingerprint(one)

# By expanding the scope of inspection to '/', we include the implementation of
# other libraries, e.g. the json module (used by foo.three())
# TODO Write a good test case for this. Currently this is pretty
#      non-deterministic because it depends on the python environment.
# print(f"\nFingerprint of one() with root='/': {func_fingerprint_hash(one, root='/')}")


announce("@astrocache.cache()")

astrocache.clear_cache()

@astrocache.cache()
def cached_func(x, **kwargs):
    print("EXECUTED")
    return one(x, 1)

print("Using the following definition:")
print(inspect.getsource(cached_func))

print("Calling cached_func(100) for the first time...")
print(cached_func(100))

print("\nCalling cached_func(100) again...")
print(cached_func(100))

print("\nChanging the implementation of make_thing(100)...")
def make_thing(a):
    return a + 3

print("\nCalling cached_func(100)...")
print(cached_func(100))

print("\nCalling cached_func(100)...")
print(cached_func(100))

print("\nCalling cached_func(999)...")
print(cached_func(999))

print("\nCalling cached_func(999)...")
print(cached_func(999))

print("\nCalling cached_func(999, foo=True)...")
print(cached_func(999, foo=True))

print("\nCalling cached_func(999, foo=True)...")
print(cached_func(999, foo=True))

announce("no_cache")

print("Calling cached_func(999, foo=True, no_cache=True)...")
print(cached_func(999, foo=True, no_cache=True))

print("\nCalling cached_func(999, foo=True, no_cache=True)...")
print(cached_func(999, foo=True, no_cache=True))

announce("passing functions into cached functions")

print("Calling cached_func(100, fn=make_thing)...")
print(cached_func(100, fn=make_thing))

print("\nCalling cached_func(100, fn=make_thing)...")
print(cached_func(100, fn=make_thing))

print("\nChanging implementation of make_thing()")
def make_thing(x):
    return x + 2

print("\nCalling cached_func(100, fn=make_thing)...")
print(cached_func(100, fn=make_thing))

print("\nMaking sure cache_id is deterministic across processes when args include functions")
print("_get_cache_id(make_thing, [make_thing], dict(fn=make_thing))")
print(astrocache._get_cache_id(make_thing, [make_thing], dict(fn=make_thing)))

announce("exceptions")

@astrocache.cache(root='/')
def root_fn(a):
    return json.dumps(a)
print("Using the following definition:")
print(inspect.getsource(root_fn))
with catch_exception():
    print("Calling root_fn(1)")
    print(root_fn(1))

with catch_exception():
    print("\nget_cache_id(make_thing, [[1]], {})")
    print(astrocache._get_cache_id(make_thing, [[1]], {}))

with catch_exception():
    print("\nget_cache_id(make_thing, [[0]], {})")
    print(astrocache._get_cache_id(make_thing, [[0]], {}))

with catch_exception():
    print("\nget_cache_id(make_thing, [[1]], {})")
    print(astrocache._get_cache_id(make_thing, [[1]], {}))
