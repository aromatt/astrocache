# funcache [![Build Status](https://app.travis-ci.com/aromatt/funcache.svg?branch=main)](https://app.travis-ci.com/aromatt/funcache)
Durable, implementation-aware memoization for Python functions.

## What is this?
This library provides the decorator `@funcache.cache` which adds
[memoization](https://en.wikipedia.org/wiki/Memoization) to the decorated function.
The cache is persisted to disk.

## So, what?
*The cache key includes the function's implementation*.

This means that the cache will refresh any time you change the implementation of the function.

Here's an example.
```python
@funcache.cache()
def my_function(foo, bar):
    return expensive_operation(foo) + bar
```
This creates an on-disk cache for `my_function`, so that repeated calls with the
same arguments avoid doing the same expensive work over and over.

But what if you change the implementation of `my_function`?
```python
@funcache.cache()
def my_function(foo, bar):
    return expensive_operation(foo) + bar * 2
```
Your cache entries are no longer valid.

Luckily, `funcache` knows the implementation has changed. The cache will be updated
the next time you call `my_function`.

This treatment extends to any function called by `my_function` as well. In this case,
`expensive_operation` (and any functions called by `expensive_operation`, etc).

## Why is this useful?
As an example, imagine you're rapidly iterating on a program or notebook that
processes data in several expensive steps, or uses a rate-limited API. You can
benefit from durable memoization here, but you don't want to have to remember to
clear the various cache entries as you iterate. This would be especially cumbersome
if you were iterating on any shared utility functions as well.

## Limitations
In general, there is one exception to the behavior described above.

Other functions referenced within your decorated function are only included in the cache
key if they are called directly, passed in, or defined in your cached function.

### Examples
#### ✅ Passing a function as a parameter
```python
@funcache.cache()
def cached_function(referenced_function):
    foo(referenced_function)
```

#### ✅ Calling a function directly
```python
@funcache.cache()
def cached_function(referenced_function):
    referenced_function(1)
```

#### ✅ Defining a function within the cached function
```python
@funcache.cache()
def cached_function():
    def referenced_function():
        return 1
    foo(referenced_function)
```

#### ❌ Assigning a function from outer scope to a variable (only)
```python
@funcache.cache()
def cached_function():
    foo = referenced_function
```

#### ❌ Passing a function from outer scope to a called function (only)
```python
@funcache.cache()
def cached_function():
    foo(referenced_function)
```

## Related projects

  * [joblib](https://github.com/joblib/joblib)
