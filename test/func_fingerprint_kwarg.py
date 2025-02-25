#!/usr/bin/env python3
# snapshot_extension=.md

import inspect

import util
import astrocache


########################
# FUNCTIONS UNDER TEST #
########################

def foo(x):
    return x + 1

def bar(fn=foo):
    return fn(1)


#######################
# TESTING STARTS HERE #
#######################


print("""
This test covers the scenario in which a function is passed as a keyword
argument to another function, then called by its kwarg parameter name.

We are interested in whether the function's fingerprint hash is affected by
changes to the passed function's source code.
""")


util.h2("Definitions")
util.code_block(inspect.getsource(foo))
util.code_block(inspect.getsource(bar))


util.h2("Initial fingerprint for `bar()`")
util.print_fingerprint(bar)


util.h2("Change behavior of `foo()`")
def foo(x):
    return x + 2
util.code_block(inspect.getsource(foo))
util.print_fingerprint(bar)
