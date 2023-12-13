
# Function fingerprint

These tests show how a function's fingerprint hash is affected by changes to its
source code.

## Definitions
```
# (This is other_module.py)
import json

def other_fn(h):
    return json.dumps(h)
```
```
def call_other_module(c):
    # Call a function in a different module
    return other_module.other_fn({'a': c + 1})
```
```
def increment(a):
    return a + 1
```
```
def nested_function_def():
    def blah(x):
        return x + 1
```
```
def nested_class_def():
    class DefInFunc:
        def __init__(self, a):
            self.thing = increment(a)
    return DefInFunc
```
```
def fn_to_assign(x):
    return x + 1
```
```
def fn_to_pass(x):
    return x * 1
```
```
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
```
Fingerprint hash for `one()`: `2844203ec8e932a051f80dcc36554193`

## Add a comment to `increment()`
```
def increment(a):
    # comment
    return a + 1
```
Fingerprint hash for `one()`: `2844203ec8e932a051f80dcc36554193`

## Change formatting in `increment()`
```
def increment(a):
    # comment

    return (a + \
            1)
```
Fingerprint hash for `one()`: `2844203ec8e932a051f80dcc36554193`

## Change behavior of `increment()`
```
def increment(a):
    return a + 2
```
Fingerprint hash for `one()`: `7bec3656aaa21534a71cbbe0dd846c5b`

## Change implementation of `fn_to_assign()`

TODO support this! fingerprint should change
```
def fn_to_assign(x):
    return x + 2
```
Fingerprint hash for `one()`: `7bec3656aaa21534a71cbbe0dd846c5b`

## Change implementation of `fn_to_pass()`

TODO support this! fingerprint should change
```
def fn_to_pass(x):
    return x * 2
```
Fingerprint hash for `one()`: `7bec3656aaa21534a71cbbe0dd846c5b`

# `@astrocache.cache()`

## Definitions
```
@astrocache.cache()
def cached_func(x, **kwargs):
    print("EXECUTED")
    return one(x, 1)
```

## Basic memoization
EXECUTED
```
>>> cached_func(100)
{"a": 102}```
```
>>> cached_func(100)
{"a": 102}```

## Change behavior of `increment(100)`
EXECUTED
```
>>> cached_func(100)
{"a": 102}```
```
>>> cached_func(100)
{"a": 102}```

## Change args
EXECUTED
```
>>> cached_func(999)
{"a": 1001}```
```
>>> cached_func(999)
{"a": 1001}```

## Add kwarg
EXECUTED
```
>>> cached_func(999, foo=True)
{"a": 1001}```
```
>>> cached_func(999, foo=True)
{"a": 1001}```

## Use no_cache
EXECUTED
```
>>> cached_func(999, foo=True, no_cache=True)
{"a": 1001}```

## Are functions passed into cached function included in fingerprint?
EXECUTED
```
>>> cached_func(100, func=increment)
{"a": 102}```
```
>>> cached_func(100, func=increment)
{"a": 102}```

Change behavior of increment()
```
def increment(x):
    return x + 2
```
EXECUTED
```
>>> cached_func(100, func=increment)
{"a": 102}```

## Make sure cache_id is deterministic across processes when args include functions
```
>>> _get_cache_id('increment', ['increment'], {'fn': 'increment'})
5cae25d3b1e7beb9239e92f85cfa53cf```

# Exceptions

## Definitions
```
@astrocache.cache(root='/')
def root_fn(a):
    return json.dumps(a)
```

## Calling a cached function with root='/'
```
>>> root_fn(1)
ValueError: Unable to find source for function _json.encode_basestring_ascii```

## Can args include lists?
```
>>> _get_cache_id('increment', [[1]], {})
2858e5cd05a2c2e1f7cba0fae210ba0e```

## Can args include dicts?
```
>>> _get_cache_id('increment', [{1: 2}], {})
181c89cd97e258c14c4c4d4dec6aae24```

## Can args include sets?
```
>>> _get_cache_id('increment', [{1}], {})
2bd7d467ef063b8d4912864c83881180```

## Can args include None?
```
>>> _get_cache_id('increment', [None], {})
76db4caa41a76e51a6cf0e81c147f315```

## Definitions
```
class MyClass:
    def __init__(self, a): self.a = a
    def __hash__(self): return self.a
```

## Can args include classes?
```
>>> _get_cache_id('increment', ['MyClass'], {})
ValueError: Unable to find source for function __main__.MyClass```

## Can args include instances of user-defined classes?
```
>>> _get_cache_id('increment', ['<MyClass instance>'], {})
0ab4a68bf6ac6d3cfe20e6d7308408a2```
