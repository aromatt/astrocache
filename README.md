# funcache [![Build Status](https://app.travis-ci.com/aromatt/funcache.svg?branch=main)](https://app.travis-ci.com/aromatt/funcache)
Durable memoization that automatically refreshes as you update your source code.

## What is this?
This library provides [memoization](https://en.wikipedia.org/wiki/Memoization) for
Python functions. This cache is persisted to disk, and is sensitive not only to the
function's inputs, but also to its *implementation* (recursively).

Here's an example:

```python
import funcache

@funcache.cache()
def foo(a, b):
    return slow_fn(a) + b
```
This creates an on-disk cache for `foo`, which avoids doing the same
expensive work more than once for a given input.

But what if you change the implementation of `foo`?

```python
@funcache.cache()
def foo(a, b):
    return slow_fn(a) + b * 2
```
Your cache entries are no longer valid because the behavior of `foo` has changed.

Luckily, `funcache` is aware of this. It will update the cache next time you call
`foo`.

This treatment extends to any function called by `foo` as well. In this case,
`slow_fn` (and any functions called by `slow_fn`, etc).

## How is this useful?
As an example, imagine you're rapidly iterating on a program or notebook that
processes data in several expensive steps, or hits a usage-limited API.

Memoization could make you more productive, but you'd have to remember to clear the
various cache entries as you iterated on your code. This would be especially cumbersome
if you memoized shared library functions.

This library automates this for you, allowing you to rapidly iterate, aided by
memoization, without having to worry about clearing the cache.

## Limitation: referenced functions
While `funcache` handles most situations in application code, there is a gotcha
related to referencing functions as values.

Other functions referenced within your decorated function are only inspected
if they are called, passed in, or defined in your cached function.

Here are some examples to illustrate this:

✅ Calling a function
```python
@funcache.cache()
def foo(referenced_function):
    # referenced_function will be inspected
    referenced_function(1)
```

✅ Passing a function as a parameter
```python
@funcache.cache()
def foo(referenced_function):
    # referenced_function will be inspected
    foo(referenced_function)
```

✅ Defining a function within the cached function
```python
@funcache.cache()
def foo():
    # referenced_function will be inspected
    def referenced_function():
        return 1
    foo(referenced_function)
```

❌ Assigning a function from outer scope to a variable (only)
```python
@funcache.cache()
def foo():
    # referenced_function will NOT be inspected
    foo = referenced_function
```

❌ Passing a function from outer scope to a called function (only)
```python
@funcache.cache()
def foo():
    # referenced_function will NOT be inspected
    foo(referenced_function)
```

## Related projects

  * [joblib](https://github.com/joblib/joblib)
