# funcache [![Build Status](https://app.travis-ci.com/aromatt/funcache.svg?branch=main)](https://app.travis-ci.com/aromatt/funcache)
Durable memoization that automatically refreshes as you update your source code.

## What is this?
This library provides [memoization](https://en.wikipedia.org/wiki/Memoization) for
Python functions. This cache is persisted to disk, and is sensitive not only to the 
function's inputs, but also to its *implementation*.

Here's an example:

```python
@funcache.cache()
def my_function(foo, bar):
    return expensive_operation(foo) + bar
```
This creates an on-disk cache for `my_function`, which avoids doing the same
expensive work more than once for a given input.

But what if you change the implementation of `my_function`?
```python
@funcache.cache()
def my_function(foo, bar):
    return expensive_operation(foo) + bar * 2
```
Your cache entries are no longer valid.

Luckily, `funcache` knows the implementation has changed. The cache will be updated
next time you call `my_function`.

This treatment extends to any function called by `my_function` as well. In this case,
`expensive_operation` (and any functions called by `expensive_operation`, etc).

## How is this useful?
As an example, imagine you're rapidly iterating on a program or notebook that
processes data in several expensive steps, or hits a usage-limited API.

Memoization could make you more productive, but you'd have to remember to clear the
various cache entries as you iterated on your code. This would be especially cumbersome
if you memoized shared library functions.

This library automates this for you, allowing you to rapidly iterate, aided by memoization,
without having to worry about clearing the cache.

## Limitations around referenced functions
In general, there is one exception to the behavior described above.

Other functions referenced within your decorated function are only inspected
if they are called, passed in, or defined in your cached function.

Here are some examples to illustrate this:

✅ Calling a function
```python
@funcache.cache()
def cached_function(referenced_function):
    # referenced_function will be inspected
    referenced_function(1)
```

✅ Passing a function as a parameter
```python
@funcache.cache()
def cached_function(referenced_function):
    # referenced_function will be inspected
    foo(referenced_function)
```

✅ Defining a function within the cached function
```python
@funcache.cache()
def cached_function():
    # referenced_function will be inspected
    def referenced_function():
        return 1
    foo(referenced_function)
```

❌ Assigning a function from outer scope to a variable (only)
```python
@funcache.cache()
def cached_function():
    # referenced_function will NOT be inspected
    foo = referenced_function
```

❌ Passing a function from outer scope to a called function (only)
```python
@funcache.cache()
def cached_function():
    # referenced_function will NOT be inspected
    foo(referenced_function)
```

## Related projects

  * [joblib](https://github.com/joblib/joblib)
