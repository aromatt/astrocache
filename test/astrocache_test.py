#!/usr/bin/env python3

import inspect
import json
import time
import textwrap
import types
from contextlib import contextmanager
from typing import Callable

import astrocache
import foo

##########################
# TEST UTILITY FUNCTIONS #
##########################

def announce(msg):
    print("\n")
    print('#' * (len(msg) + 4))
    print('# ' + msg + ' #')
    print('#' * (len(msg) + 4))


def get_fn_name(fn):
    if hasattr(fn, '__self__'):
        owner = fn.__self__
        if hasattr(owner, '__name__'):
            owner_name = owner.__name__
        else:
            owner_name = str(owner)
        return f"{owner_name}.{fn.__name__}"
    else:
        return fn.__qualname__


def sanitize(data):
    if isinstance(data, (types.GeneratorType, list, map, filter, tuple)):
        return [sanitize(x) for x in data]
    elif isinstance(data, dict):
        return {k: sanitize(v) for k, v in data.items()}
    else:
        if isinstance(data, Callable):
            return get_fn_name(data)
        else:
            return data


def invoke(fn, *args, **kwargs):
    name = get_fn_name(fn)
    param_str = ', '.join([*map(repr, sanitize(args)),
                           *[f"{k}={v}" for k,v in sanitize(kwargs).items()]])
    print(f">>> {name}({param_str})")
    try:
        result = fn(*args, **kwargs)
    except Exception as e:
        result = f"{type(e).__name__}: {e}"
    print(result)


def func_fingerprint_hash(func, **kwargs):
    return astrocache._make_hash(astrocache._func_fingerprint(one, **kwargs))


def print_fingerprint(func):
    print(f"Fingerprint hash for {func.__name__}(): {func_fingerprint_hash(func)}")


def remark(msg):
    print(f"\n# {msg}")


########################
# FUNCTIONS UNDER TEST #
########################

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


# TODO split this up... this is pretty cluttered
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


#######################
# TESTING STARTS HERE #
#######################

announce("Function implementation fingerprint")

remark("Using the following definitions:")
print("```")
print(inspect.getsource(foo.three))
print(inspect.getsource(two))
print(inspect.getsource(make_thing))
print(inspect.getsource(nested_function_def))
print(inspect.getsource(nested_class_def))
print(inspect.getsource(fn_to_assign))
print(inspect.getsource(fn_to_pass))
print(inspect.getsource(one))
print("```")


remark("What is the fingerprint of one()?")
print_fingerprint(one)


remark("Adding a comment to make_thing()")
def make_thing(a):
    # comment
    return a + 1
print_fingerprint(one)


remark("Change formatting in make_thing()")
def make_thing(a):
    # comment

    return (a + \
            1)
print_fingerprint(one)


remark("Change behavior of make_thing()")
# Lineage: one() -> nested_function_def() -> class Foo -> __init__ -> make_thing()
def make_thing(a):
    return a + 2
print_fingerprint(one)


remark("Change implementation of fn_to_assign(). "
       "TODO support this! fingerprint should change")
def fn_to_assign(x):
    return x + 2
print_fingerprint(one)


remark("Change implementation of fn_to_pass(). "
       "TODO support this! fingerprint should change")
def fn_to_pass(x):
    return x * 2
print_fingerprint(one)


# TODO Write a good test case for this. Currently this is pretty
#      non-deterministic because it depends on the python environment.
# By expanding the scope of inspection to '/', we include the implementation of
# other libraries, e.g. the json module (used by foo.three())
# print(f"\nFingerprint of one() with root='/': {func_fingerprint_hash(one, root='/')}")


announce("@astrocache.cache()")
astrocache.clear_cache()


@astrocache.cache()
def cached_func(x, **kwargs):
    print("EXECUTED")
    return one(x, 1)


remark("Using the following definition:")
print("```")
print(inspect.getsource(cached_func))
print("```")


remark("Testing basic memoization")
invoke(cached_func, 100)
invoke(cached_func, 100)


remark("Change behavior of make_thing(100)")
def make_thing(a):
    return a + 3
invoke(cached_func, 100)
invoke(cached_func, 100)


remark("Different args")
invoke(cached_func, 999)
invoke(cached_func, 999)


remark("Adding kwarg")
invoke(cached_func, 999, foo=True)
invoke(cached_func, 999, foo=True)


remark("Using no_cache")
invoke(cached_func, 999, foo=True, no_cache=True)


remark("Are functions passed into cached function included in fingerprint?")
invoke(cached_func, 100, func=make_thing)
invoke(cached_func, 100, func=make_thing)
remark("Change behavior of make_thing()")
def make_thing(x):
    return x + 2
invoke(cached_func, 100, func=make_thing)


remark("Making sure cache_id is deterministic across processes when args include functions")
print("_get_cache_id(make_thing, [make_thing], dict(fn=make_thing))")
print(astrocache._get_cache_id(make_thing, [make_thing], dict(fn=make_thing)))


announce("Exceptions")


@astrocache.cache(root='/')
def root_fn(a):
    return json.dumps(a)

remark("Using the following definition:")
print("```")
print(inspect.getsource(root_fn))
print("```")


remark("Calling a cached function with root='/'")
invoke(root_fn, 1)


remark("Can args include lists?")
invoke(astrocache._get_cache_id, make_thing, [[1]], {})


remark("Can args include dicts?")
invoke(astrocache._get_cache_id, make_thing, [{1: 2}], {})


remark("Can args include sets?")
invoke(astrocache._get_cache_id, make_thing, [set([1])], {})


class Foo:
    def __init__(self, a): self.a = a
    def __repr__(self): return f'Foo({self.a})'
    def __hash__(self): hash(self.a)


remark("Using the following definition:")
print("```")
print(inspect.getsource(Foo))
print("```")


remark("Can args include classes?")
invoke(astrocache._get_cache_id, make_thing, [Foo], {})


remark("Can args include instances of hashable user-defined classes?")
invoke(astrocache._get_cache_id, make_thing, [Foo(1)], {})
