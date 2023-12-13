#!/usr/bin/env python3
# snapshot_extension=.md

import inspect

import util
import astrocache


########################
# FUNCTIONS UNDER TEST #
########################


def increment(a):
    return a + 1


def nested_class_def():
    class DefInFunc:
        def __init__(self, a):
            self.thing = increment(a)
    return DefInFunc


def foo():
    nested_class_def()


#######################
# TESTING STARTS HERE #
#######################


print("""
This test shows how a function's fingerprint hash is affected by
deeper changes to its source code.
""")


util.h2("Definitions")
util.code_block(inspect.getsource(increment))
util.code_block(inspect.getsource(nested_class_def))
util.code_block(inspect.getsource(foo))


util.h2("Initial fingerprint for `foo()`")
util.print_fingerprint(foo)


util.h2("Change behavior of `increment()`")
print("""
Lineage: ```
foo() -> nested_function_def() -> class DefInFunc -> __init__ -> increment()
```""")
def increment(a):
    return a + 2
util.code_block(inspect.getsource(increment))
util.print_fingerprint(foo)
