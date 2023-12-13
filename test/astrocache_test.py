#!/usr/bin/env python3
# snapshot_extension=.md

import inspect
import json

import astrocache
import other_module
import util


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

util.h1("Function fingerprint")
util.text_block("These tests show how a function's fingerprint hash is affected by "
           "changes to its source code.")

util.h2("Definitions")
util.code_block("# (This is other_module.py)\n" +
           inspect.getsource(other_module))
util.code_block(inspect.getsource(call_other_module))
util.code_block(inspect.getsource(increment))
util.code_block(inspect.getsource(nested_function_def))
util.code_block(inspect.getsource(nested_class_def))
util.code_block(inspect.getsource(fn_to_assign))
util.code_block(inspect.getsource(fn_to_pass))
util.code_block(inspect.getsource(one))


util.print_fingerprint(one)


util.h2("Add a comment to `increment()`")
def increment(a):
    # comment
    return a + 1
util.code_block(inspect.getsource(increment))
util.print_fingerprint(one)


util.h2("Change formatting in `increment()`")
def increment(a):
    # comment

    return (a + \
            1)
util.code_block(inspect.getsource(increment))
util.print_fingerprint(one)


util.h2("Change behavior of `increment()`")
# Lineage: one() -> nested_function_def() -> class DefInFunc -> __init__ -> increment()
def increment(a):
    return a + 2
util.code_block(inspect.getsource(increment))
util.print_fingerprint(one)


util.h2("Change implementation of `fn_to_assign()`")
util.text_block("TODO support this! fingerprint should change")
def fn_to_assign(x):
    return x + 2
util.code_block(inspect.getsource(fn_to_assign))
util.print_fingerprint(one)


util.h2("Change implementation of `fn_to_pass()`")
util.text_block("TODO support this! fingerprint should change")
def fn_to_pass(x):
    return x * 2
util.code_block(inspect.getsource(fn_to_pass))
util.print_fingerprint(one)


# TODO Write a good test case for this. Currently this is pretty
#      non-deterministic because it depends on the python environment.
# By expanding the scope of inspection to '/', we include the implementation of
# other libraries, e.g. the json module (used by other_module.three())
# print(f"\nFingerprint of one() with root='/': {func_fingerprint_hash(one, root='/')}")


util.h1("`@astrocache.cache()`")
astrocache.clear_cache()


@astrocache.cache()
def cached_func(x, **kwargs):
    print("EXECUTED")
    return one(x, 1)


util.h2("Definitions")
util.code_block(inspect.getsource(cached_func))


util.h2("Basic memoization")
util.invoke(cached_func, 100)
util.invoke(cached_func, 100)


util.h2("Change behavior of `increment(100)`")
def increment(a):
    return a + 3
util.invoke(cached_func, 100)
util.invoke(cached_func, 100)


util.h2("Change args")
util.invoke(cached_func, 999)
util.invoke(cached_func, 999)


util.h2("Add kwarg")
util.invoke(cached_func, 999, foo=True)
util.invoke(cached_func, 999, foo=True)


util.h2("Use no_cache")
util.invoke(cached_func, 999, foo=True, no_cache=True)


util.h2("Are functions passed into cached function included in fingerprint?")
util.invoke(cached_func, 100, func=increment)
util.invoke(cached_func, 100, func=increment)
util.text_block("Change behavior of increment()")
def increment(x):
    return x + 2
util.code_block(inspect.getsource(increment))
util.invoke(cached_func, 100, func=increment)


util.h2("Make sure cache_id is deterministic across processes when args include functions")
util.invoke(astrocache._get_cache_id, increment, [increment], dict(fn=increment))


util.h1("Exceptions")


@astrocache.cache(root='/')
def root_fn(a):
    return json.dumps(a)

util.h2("Definitions")
util.code_block(inspect.getsource(root_fn))


util.h2("Calling a cached function with root='/'")
util.invoke(root_fn, 1)


util.h2("Can args include lists?")
util.invoke(astrocache._get_cache_id, increment, [[1]], {})


util.h2("Can args include dicts?")
util.invoke(astrocache._get_cache_id, increment, [{1: 2}], {})


util.h2("Can args include sets?")
util.invoke(astrocache._get_cache_id, increment, [set([1])], {})


util.h2("Can args include None?")
util.invoke(astrocache._get_cache_id, increment, [None], {})


class MyClass:
    def __init__(self, a): self.a = a
    def __hash__(self): return self.a

util.h2("Definitions")
util.code_block(inspect.getsource(MyClass))


util.h2("Can args include classes?")
util.invoke(astrocache._get_cache_id, increment, [MyClass], {})


util.h2("Can args include instances of user-defined classes?")
util.invoke(astrocache._get_cache_id, increment, [MyClass(1)], {})
