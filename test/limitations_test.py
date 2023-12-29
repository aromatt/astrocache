#!/usr/bin/env python3
# snapshot_extension=.md

import inspect

import util
import astrocache


util.h1("Limitations")

util.text_block("""
Astrocache's AST-sensitivity covers most situations you might expect.

However, functions referenced by your cached function are only considered part
of its AST if one or more of these criteria are met:
1. Cached function calls referenced function
2. Cached function defines referenced function
3. Cached function receives referenced function as a parameter

By contrast, the following kinds of references (on their own) do _not_ result in
the referenced function being considered part of your cached function's AST:
* Cached function assigns referenced function to a variable
* Cached function passes referenced function as an argument

This test case documents the behavior in each of these scenarios.

We track material changes to a function's AST via its fingerprint hash, which is
part of its cache key.
""")

def print_fingerprint_changed(func, old):
    new = util.func_fingerprint_hash(func)
    message = f"Fingerprint for `{func.__name__}()`: `{new}`"
    if old is not None:
        status = 'unchanged' if new == old else 'changed'
        message += f" ({status})"
    util.text_block(message)
    return new


def print_cache_id_changed(func, args, kwargs, old):
    new = astrocache._get_cache_id(fun, args, kwargs)
    param_str = util.get_param_str(args, kwargs)
    message = f"Cache ID for `{func.__name__}({param_str})`: `{new}`"
    if old is not None:
        status = 'unchanged' if new == old else 'changed'
        message += f" ({status})"
    text_block(message)
    return new


###############################################################################
util.h2("Calling a function (criterion 1)")
util.text_block("""
Here, `called_fn()` is invoked by `foo()`, so it meets criterion 1.
""")

def called_fn(x):
    return x + 1

def foo():
    called_fn()

util.code_block(inspect.getsource(called_fn))
util.code_block(inspect.getsource(foo))

foo_fp = print_fingerprint_changed(foo, None)

util.text_block("Change implementation of `called_fn()`")
def called_fn(x):
    return x + 2
util.code_block(inspect.getsource(called_fn))
foo_fp = print_fingerprint_changed(foo, foo_fp)


###############################################################################
util.h2("Defining a function (criterion 2)")
util.text_block("""
Here, `defined_fn()` is defined within `foo()`, so it meets criterion 2.
""")

def foo():
    def defined_fn():
        return x + 1

util.code_block(inspect.getsource(foo))

foo_fp = print_fingerprint_changed(foo, None)

util.text_block("Change implementation of `defined_fn()`")
def foo():
    def defined_fn():
        return x + 2
util.code_block(inspect.getsource(foo))
foo_fp = print_fingerprint_changed(foo, foo_fp)


###############################################################################
util.h2("Assigning a function to a variable")
util.text_block("""
Here, `assigned_fn()` is assigned to a variable within `foo()`, but none of the
criteria are met.
""")

def assigned_fn(x):
    return x + 1

def foo():
    # Assign a function to a variable, but don't call it
    fn = assigned_fn

util.code_block(inspect.getsource(assigned_fn))
util.code_block(inspect.getsource(foo))

foo_fp = print_fingerprint_changed(foo, None)

util.text_block("Change implementation of `assigned_fn()`")
def assigned_fn():
    return x + 2
util.code_block(inspect.getsource(assigned_fn))
foo_fp = print_fingerprint_changed(foo, foo_fp)


###############################################################################
util.h2("Passing a function to a function call")
util.text_block("""
Here, `passed_fn()` is passed to another function by `foo()`, but none of the
criteria are met.
""")

def passed_fn(x):
    return x + 1

def foo():
    # Pass a function as an argument, but don't call it
    print(passed_fn)

util.code_block(inspect.getsource(passed_fn))
util.code_block(inspect.getsource(foo))

foo_fp = print_fingerprint_changed(foo, None)

util.text_block("Change implementation of `passed_fn()`")
def passed_fn():
    return x + 2
util.code_block(inspect.getsource(passed_fn))
foo_fp = print_fingerprint_changed(foo, foo_fp)


###############################################################################
util.h2("Workaround (criterion 3)")
util.text_block("""
If your use case doesn't meet either of the first two criteria, you can force
criterion 3 by requiring the caller to pass it to your function as an argument,
even if this isn't otherwise necessary.

Then, when your cached function is invoked, the referenced function will be
mixed into the cache key along with the other arguments.
""")

def received_fn(x):
    return x + 1

def foo(fn=received_fn):
    return True

util.code_block(inspect.getsource(received_fn))
util.code_block(inspect.getsource(foo))

foo_fp = print_fingerprint_changed(foo, None)

util.text_block("Change implementation of `received_fn()`")
def received_fn():
    return x + 2
util.code_block(inspect.getsource(received_fn))
foo_fp = print_fingerprint_changed(foo, foo_fp)
