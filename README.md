# funcache [![Build Status](https://app.travis-ci.com/aromatt/funcache.svg?branch=main)](https://app.travis-ci.com/aromatt/funcache)
Durable, implementation-aware memoization for Python functions.

## What is this?
This library provides a decorator, `@funcache.cache`, which adds [memoization](https://en.wikipedia.org/wiki/Memoization)
to the decorated function. The cache is persisted to disk.

## So, what?
*The cache key includes the function's implementation*.

### Huh?
This means that the cache will refresh any time you change the implementation of the function.

Here's an example.
```python
@funcache.cache()
def my_function(foo, bar):
    return expensive_operation(foo) + bar
```
This creates an on-disk cache for `my_function`, so that repeated calls with the 
same arguments don't cause the function to do its expensive work over and over.

But what if you change the implementation of `my_function`?
```python
@funcache.cache()
def my_function(foo, bar):
    return expensive_operation(foo) - bar
```
Your cache entries are no longer valid. 

Luckily, `funcache` knows the implementation has changed, so it will refresh the
cache the next time you call `my_function`. This treatment extends to any function
called by `my_function` as well; in this case, `expensive_operation` (and so on, 
recursively).

## How is this useful?
As an example, imagine you're rapidly iterating on a script or notebook that processes data 
in several expensive steps. You can benefit from durable memoization here, but you don't want
to have to remember to clear the various cache entries as you iterate. This would be especially
cumbersome if you were iterating on any shared utility functions as well.

## Limitations
`funcache` includes the following in its cache keys:

  * All hashable args and kwargs
  * The cached function's own implementation
  * Implementations of any functions that are:
      * Passed as args or kwargs
      * Called directly by the cached function
      * Defined within the cached function
  * Class definitions within the cached function

If you reference a function but do not call it directly or receive it as a parameter, 
then its definition will not be included in the cache key. Examples:
```python
@funcache.cache()
def my_function():
    foo = some_function
        
@funcache.cache()
def my_function():
    bar(some_function)
```
In these examples, `some_function`'s definition is not included in the cache key for `my_function`,
because `my_function` doesn't call it and it's not received as a parameter. To get around this,
you can just accept it as a parameter.
```python
@funcache.cache()
def my_function(foo, some_function):
    foo = some_function
    # or
    bar(some_function)
```

Here, `some_functions`'s implementation *will* be included in the cache key because it's received
as a parameter.

## Related projects
  
  * [joblib](https://github.com/joblib/joblib)
