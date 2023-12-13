
This test shows how a function's fingerprint hash is affected by
deeper changes to its source code.


## Definitions
```
def increment(a):
    return a + 1
```
```
def nested_class_def():
    class DefInFunc:
        def __init__(self, a):
            self.thing = increment(a)
    return DefInFunc
```
```
def foo():
    nested_class_def()
```

## Initial fingerprint for `foo()`
Fingerprint hash for `foo()`: `569edb365eda0af72967c532f60aefe2`

## Change behavior of `increment()`

Lineage: ```
foo() -> nested_function_def() -> class DefInFunc -> __init__ -> increment()
```
```
def increment(a):
    return a + 2
```
Fingerprint hash for `foo()`: `fa4d5ad33c8429772bce0698eda7398e`
