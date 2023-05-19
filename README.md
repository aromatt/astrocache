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

        @funcache.cache()
        def my_function(foo, bar):
            return expensive_operation(foo) + bar

This creates an on-disk cache for `my_function`, so that repeated calls with the 
same arguments don't cause the function to do its expensive work over and over. 
But what if you change the implementation of `my_function`?

        @funcache.cache()
        def my_function(foo, bar):
            return expensive_operation(foo) - bar
            
Your cached answers are no longer valid. 

Luckily, `funcache` knows the implementation has changed, so it will refresh the
cache the next time you call `my_function`. This treatment extends to any function
called by `my_function` as well; in this case, `expensive_operation`.

## How is this useful?
As an example, imagine you're rapidly iterating on a script or notebook that processes data 
in several expensive steps. You can benefit from durable memoization here, but you don't want
to have to remember to clear the various cache entries as you iterate. This would be especially
cumbersome if you had any shared utility functions that you're also iterating on.

## Limitations
`funcache` includes the following in its cache keys:

  * Args and kwargs. This includes the implementations of functions passed as arguments.
  * The cached function's own implementation
  * Implementations of functions called directly by the cached function
  * Implementations of functions defined within the cached function
  * Implementations of classes defined within the cached function

If you only reference a function but do not call it directly or receive it as a parameter
to your cached function, then its definition will not be included in the cache key.

        @funcache.cache()
        def my_function():
            foo = some_function
        
        @funcache.cache()
        def my_function():
            bar(some_function)
            
In these examples, `some_function`'s definition is not included in the cache key for `my_function`,
because `my_function` doesn't call it and it's not received as a parameter. To get around this,
you can just accept it as a parameter.

        @funcache.cache()
        def my_function(foo, some_function):
            foo = some_function
            # or
            bar(some_function)
            

Here, `some_functions`'s implementation *will* be included in the cache key.

## Related projects
  
  * [joblib](https://github.com/joblib/joblib)
