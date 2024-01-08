#!/usr/bin/env python3
# snapshot_extension=.md

import inspect
import json

import astrocache
import util

########################
# FUNCTIONS UNDER TEST #
########################


def scale(x):
    print('scale() called')
    return x * 2

@astrocache.cache()
def foo(a, b):
    data = {'value': scale(a) + b}
    # Include a standard library function in the implementation
    return json.dumps(data)


#######################
# TESTING STARTS HERE #
#######################


util.h2("Definitions")
util.code_block(inspect.getsource(scale))
util.code_block(inspect.getsource(foo))

astrocache.clear_cache()

util.h2("Call `foo()` twice with the same args")
util.invoke(foo, 1, 2)
util.invoke(foo, 1, 2)

util.h2("Call `foo()` with different args")
util.invoke(foo, 1, 3)

util.h2("Change implementation of `scale()`")
def scale(x):
    print('scale() called')
    return x * 3
util.code_block(inspect.getsource(scale))

util.invoke(foo, 1, 2)