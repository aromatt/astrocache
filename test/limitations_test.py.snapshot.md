
# Limitations

Astrocache's AST-sensitivity covers most situations you might expect.

However, functions referenced by your cached function are only considered part
of its AST if one or more of these criteria are met:
1. Cached function calls referenced function
2. Cached function defines referenced function
3. Cached function receives referenced function as a parameter

By contrast, the following kinds of references (on their own) do _not_ result in
the referenced function being considered part of your cached function's AST:
* Cached function assigns referenced function to a variable
* Cached function passes referenced function as an argument

This test case documents the behavior in each of these scenarios.

We track material changes to a function's AST via its fingerprint hash, which is
part of its cache key.



## Calling a function (criterion 1)

Here, `called_fn()` is invoked by `foo()`, so it meets criterion 1.


```python
def called_fn(x):
    return x + 1

```
```python
def foo():
    called_fn()

```
Fingerprint for `foo()`: `7a7d78356d0a1984713973ba84d614c6`

Change implementation of `called_fn()`

```python
def called_fn(x):
    return x + 2

```
Fingerprint for `foo()`: `fa4a73f1c976fccf7be0b12de0c4e3fd` (changed)


## Defining a function (criterion 2)

Here, `defined_fn()` is defined within `foo()`, so it meets criterion 2.


```python
def foo():
    def defined_fn():
        return x + 1

```
Fingerprint for `foo()`: `d022d2d236217777d2af9a79ec090e9a`

Change implementation of `defined_fn()`

```python
def foo():
    def defined_fn():
        return x + 2

```
Fingerprint for `foo()`: `fbbb715480e7ff9e808ff35af5a3b1d6` (changed)


## Assigning a function to a variable

Here, `assigned_fn()` is assigned to a variable within `foo()`, but none of the
criteria are met.


```python
def assigned_fn(x):
    return x + 1

```
```python
def foo():
    # Assign a function to a variable, but don't call it
    fn = assigned_fn

```
Fingerprint for `foo()`: `9c9e43b454482908af31b33a89b78364`

Change implementation of `assigned_fn()`

```python
def assigned_fn():
    return x + 2

```
Fingerprint for `foo()`: `9c9e43b454482908af31b33a89b78364` (unchanged)


## Passing a function to a function call

Here, `passed_fn()` is passed to another function by `foo()`, but none of the
criteria are met.


```python
def passed_fn(x):
    return x + 1

```
```python
def foo():
    # Pass a function as an argument, but don't call it
    print(passed_fn)

```
Fingerprint for `foo()`: `bb2fd6700a7cc4ae81ad7dafe6ac7283`

Change implementation of `passed_fn()`

```python
def passed_fn():
    return x + 2

```
Fingerprint for `foo()`: `bb2fd6700a7cc4ae81ad7dafe6ac7283` (unchanged)


## Workaround (criterion 3)

If your use case doesn't meet either of the first two criteria, you can force
criterion 3 by requiring the caller to pass it to your function as an argument,
even if this isn't otherwise necessary.

Then, when your cached function is invoked, the referenced function will be
mixed into the cache key along with the other arguments.


```python
def received_fn(x):
    return x + 1

```
```python
def foo(fn=received_fn):
    return True

```
Fingerprint for `foo()`: `0de9e84b1b762a204b3ce9bb0df64b3e`

Change implementation of `received_fn()`

```python
def received_fn():
    return x + 2

```
Fingerprint for `foo()`: `0de9e84b1b762a204b3ce9bb0df64b3e` (unchanged)

