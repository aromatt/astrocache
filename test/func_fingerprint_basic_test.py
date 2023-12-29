#!/usr/bin/env python3
# snapshot_extension=.md

import inspect

import util
import astrocache


########################
# FUNCTIONS UNDER TEST #
########################

# We will re-implement this function over the course of the test
def foo(a):
    return a + 1


#######################
# TESTING STARTS HERE #
#######################


print("""
A cached function's fingerprint hash is a component of the function's cache key.
When a function's abstract syntax tree (AST) changes, the fingerprint hash
changes too.

This test shows how a function's fingerprint hash is affected by basic changes
to its source code.
""")


util.h2("Definitions")
util.code_block(inspect.getsource(foo))


util.h2("Initial fingerprint for `foo()`")
util.print_fingerprint(foo)


util.h2("Add a comment to `foo()`")
def foo(a):
    # comment
    return a + 1
util.code_block(inspect.getsource(foo))
util.print_fingerprint(foo)


util.h2("Change formatting in `foo()`")
def foo(a):
    # comment

    return (a + \
            1)
util.code_block(inspect.getsource(foo))
util.print_fingerprint(foo)


util.h2("Change behavior of `foo()`")
def foo(a):
    return a + 2
util.code_block(inspect.getsource(foo))
util.print_fingerprint(foo)
