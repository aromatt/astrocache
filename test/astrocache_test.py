#!/usr/bin/env python3
# snapshot_extension=.md

import inspect
import json
import time
import textwrap
import types
from contextlib import contextmanager
from typing import Callable

import astrocache
import other_module

##########################
# TEST UTILITY FUNCTIONS #
##########################

# Markdown generation helpers
def h1(msg): print(f"\n# {msg}")
def h2(msg): print(f"\n## {msg}")
def h3(msg): print(f"\n### {msg}")
def code_block(code): print(f"```\n{code}```")
def text_block(msg): print('\n' + '\n'.join(textwrap.wrap(msg, width=80)))


def get_fn_name(fn):
    """Returns the name of `fn` as a deterministic string"""
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
    elif isinstance(data, Callable):
        return get_fn_name(data)
    elif type(data).__repr__ == object.__repr__:
        # Need to support classes without __repr__ implementations in order to
        # test _make_hash() properly
        return f'<{type(data).__name__} instance>'
    else:
        return data


def invoke(fn, *args, **kwargs):
    """Call `fn` with provided args and kwargs, printing the invocation and its
    result"""
    name = get_fn_name(fn)
    param_str = ', '.join([*map(repr, sanitize(args)),
                           *[f"{k}={v}" for k,v in sanitize(kwargs).items()]])
    command = f">>> {name}({param_str})"
    try:
        result = fn(*args, **kwargs)
    except Exception as e:
        result = f"{type(e).__name__}: {e}"
    code_block(f"{command}\n{result}")


def func_fingerprint_hash(func, **kwargs):
    return astrocache._make_hash(astrocache._func_fingerprint(one, **kwargs))


def print_fingerprint(func):
    print(f"Fingerprint hash for `{func.__name__}()`: `{func_fingerprint_hash(func)}`")


########################
# FUNCTIONS UNDER TEST #
########################


def increment(a):
    return a + 1


def nested_function_def():
    def blah(x):
        return x + 1


def nested_class_def():
    class DefInFunc:
        def __init__(self, a):
            self.thing = increment(a)
    return DefInFunc


def fn_to_assign(x):
    return x + 1


def fn_to_pass(x):
    return x * 1


def think_about_function(fn):
    thoughts = [fn]
    return fn


def call_other_module(c):
    # Call a function in a different module
    return other_module.other_fn({'a': c + 1})



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
    return call_other_module(a + b)


#######################
# TESTING STARTS HERE #
#######################

h1("Function fingerprint")
text_block("These tests show how a function's fingerprint hash is affected by "
           "changes to its source code.")

h2("Definitions")
code_block("# (This is other_module.py)\n" +
           inspect.getsource(other_module))
code_block(inspect.getsource(call_other_module))
code_block(inspect.getsource(increment))
code_block(inspect.getsource(nested_function_def))
code_block(inspect.getsource(nested_class_def))
code_block(inspect.getsource(fn_to_assign))
code_block(inspect.getsource(fn_to_pass))
code_block(inspect.getsource(one))


print_fingerprint(one)


h2("Add a comment to `increment()`")
def increment(a):
    # comment
    return a + 1
code_block(inspect.getsource(increment))
print_fingerprint(one)


h2("Change formatting in `increment()`")
def increment(a):
    # comment

    return (a + \
            1)
code_block(inspect.getsource(increment))
print_fingerprint(one)


h2("Change behavior of `increment()`")
# Lineage: one() -> nested_function_def() -> class DefInFunc -> __init__ -> increment()
def increment(a):
    return a + 2
code_block(inspect.getsource(increment))
print_fingerprint(one)


h2("Change implementation of `fn_to_assign()`")
text_block("TODO support this! fingerprint should change")
def fn_to_assign(x):
    return x + 2
code_block(inspect.getsource(fn_to_assign))
print_fingerprint(one)


h2("Change implementation of `fn_to_pass()`")
text_block("TODO support this! fingerprint should change")
def fn_to_pass(x):
    return x * 2
code_block(inspect.getsource(fn_to_pass))
print_fingerprint(one)


# TODO Write a good test case for this. Currently this is pretty
#      non-deterministic because it depends on the python environment.
# By expanding the scope of inspection to '/', we include the implementation of
# other libraries, e.g. the json module (used by other_module.three())
# print(f"\nFingerprint of one() with root='/': {func_fingerprint_hash(one, root='/')}")


h1("`@astrocache.cache()`")
astrocache.clear_cache()


@astrocache.cache()
def cached_func(x, **kwargs):
    print("EXECUTED")
    return one(x, 1)


h2("Definitions")
code_block(inspect.getsource(cached_func))


h2("Basic memoization")
invoke(cached_func, 100)
invoke(cached_func, 100)


h2("Change behavior of `increment(100)`")
def increment(a):
    return a + 3
invoke(cached_func, 100)
invoke(cached_func, 100)


h2("Change args")
invoke(cached_func, 999)
invoke(cached_func, 999)


h2("Add kwarg")
invoke(cached_func, 999, foo=True)
invoke(cached_func, 999, foo=True)


h2("Use no_cache")
invoke(cached_func, 999, foo=True, no_cache=True)


h2("Are functions passed into cached function included in fingerprint?")
invoke(cached_func, 100, func=increment)
invoke(cached_func, 100, func=increment)
text_block("Change behavior of increment()")
def increment(x):
    return x + 2
code_block(inspect.getsource(increment))
invoke(cached_func, 100, func=increment)


h2("Make sure cache_id is deterministic across processes when args include functions")
invoke(astrocache._get_cache_id, increment, [increment], dict(fn=increment))


h1("Exceptions")


@astrocache.cache(root='/')
def root_fn(a):
    return json.dumps(a)

h2("Definitions")
code_block(inspect.getsource(root_fn))


h2("Calling a cached function with root='/'")
invoke(root_fn, 1)


h2("Can args include lists?")
invoke(astrocache._get_cache_id, increment, [[1]], {})


h2("Can args include dicts?")
invoke(astrocache._get_cache_id, increment, [{1: 2}], {})


h2("Can args include sets?")
invoke(astrocache._get_cache_id, increment, [set([1])], {})


h2("Can args include None?")
invoke(astrocache._get_cache_id, increment, [None], {})


class MyClass:
    def __init__(self, a): self.a = a
    def __hash__(self): return self.a

h2("Definitions")
code_block(inspect.getsource(MyClass))


h2("Can args include classes?")
invoke(astrocache._get_cache_id, increment, [MyClass], {})


h2("Can args include instances of user-defined classes?")
invoke(astrocache._get_cache_id, increment, [MyClass(1)], {})
