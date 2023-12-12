# astrocache [![Build Status](https://app.travis-ci.com/aromatt/funcache.svg?branch=main)](https://app.travis-ci.com/aromatt/funcache)
Durable memoization that automatically refreshes as you update your source code.

## Installation
Astrocache requires Python >= 3.9, and has no additional dependencies.

```
python3 -m pip install astrocache
```

## What is this?
This library provides disk-backed memoization for Python functions with a
surprisingly useful twist: the cache is sensitive not only to your function's inputs,
but also to its *implementation* (represented by its abstract syntax tree or AST).

If you're unfamiliar with memoization, check out the [Wikipedia
page](https://en.wikipedia.org/wiki/Memoization) and
[functools.cache](https://docs.python.org/3/library/functools.html#functools.cache)
for in-depth explanations.

### AST-sensitive memoization
```python
import astrocache

@astrocache.cache()
def foo(a, b):
    return slow_fn(a) + b
```
This creates a disk-backed cache for `foo`, which prevents `foo` from performing the
same work more than once for a given input. So far, this is pretty standard; many
other libraries offer the same thing.

But what if you change the behavior of `foo`?

```python
@astrocache.cache()
def foo(a, b):
    return slow_fn(a) + b * 2
```
Your cache entries are no longer valid.

Luckily, astrocache is aware of this. It will create new cache entries for the new
version of `foo`.

This treatment extends recursively to any function called by `foo` as well. In this
case, changes to `slow_fn` (and to functions called by `slow_fn`, etc) will also
invalidate cache entries for `foo`.

## How does it work?
Astrocache creates a fingerprint of your function's abstract syntax tree (AST)
using the [ast](https://docs.python.org/3/library/ast.html) module from the standard
library.

When your function is called, this fingerprint is combined with the provided
arguments to create a cache key.

## How is this useful?
This is particularly useful in highly interactive workflows, e.g. during rapid
iteration or in a notebook setting. Many libraries provide some form of memoization,
but none (as far as I know) manage this kind of cache invalidation for you.

As an example, imagine you're rapidly iterating on a script that processes data in
several expensive steps, or hits a usage-capped external API.

Memoization could certainly make you more productive, but you'd have to remember to
clear the various cache entries as you updated your code.

This library automates this for you, allowing you to take advantage of memoization
without needing to worry about clearing the cache.

## Limitations
### Referenced functions
There is a caveat regarding AST inspection of functions that are referenced, but not
invoked. Example:

```python
import astrocache

def bar(a):
    return a + 1

@astrocache.cache()
def foo(x):
    return baz(bar)
```
Here, `bar` is referenced (passed as an argument), but not invoked, by `foo`.

Functions appearing within your cached function are only included in the AST
fingerprint if your cached function does any of these:
* Calls the referenced function
* Receives the referenced function as an argument
* Contains the definition of the referenced function

Here are some examples to illustrate this:

✅ Calling a function
```python
@astrocache.cache()
def foo(referenced_function):
    # referenced_function will be included
    referenced_function(1)
```

✅ Receiving the function as an argument
```python
@astrocache.cache()
def foo(referenced_function):
    # referenced_function will be included
    foo(referenced_function)
```

✅ Defining a function within the cached function
```python
@astrocache.cache()
def foo():
    # referenced_function will be included
    def referenced_function():
        return 1
    foo(referenced_function)
```

❌ Assigning a function from outer scope to a variable (only)
```python
@astrocache.cache()
def foo():
    # referenced_function will NOT be included
    foo = referenced_function
```

❌ Passing a function from outer scope to a called function (only)
```python
@astrocache.cache()
def foo():
    # referenced_function will NOT be included
    foo(referenced_function)
```

## Related projects

### [joblib](https://github.com/joblib/joblib)
Among joblib's excellent suite of pipeline processing tools, there is a memoization
decorator similar to `@astrocache.cache()`. This decorator is also source-code-aware,
with some key differences:
* It does not inspect the function's AST, just the literal source. So it doesn't
  recursively inspect called functions, and it's sensitive to whitespace and
  comments.
* It only tracks the latest version of your function (identified by source file path
  and function name). When you update your code, the cache entries are all marked as
  dirty, and will be overwritten. With astrocache, you could return to a previous
  version of your code without losing the cache history.
* As a more mature library, it has various optimizations for large objects and
  special support for numpy arrays.

## Tests
This project uses
[baseline testing](https://nodiff.net/2023/01/introduction-to-baseline-testing).
The test scripts in the `test` directory generate text files (`test/*.snapshot*`)
that aim to serve as self-validating reference docs for astrocache.

To run the tests, use `make test`.
