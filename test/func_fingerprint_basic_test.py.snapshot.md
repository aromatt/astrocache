
A cached function's fingerprint hash is a component of the function's cache key.
When a function's abstract syntax tree (AST) changes, the fingerprint hash
changes too.

This test shows how a function's fingerprint hash is affected by basic changes
to its source code.


## Definitions
```python
def foo(a):
    return a + 1

```

## Initial fingerprint for `foo()`
Fingerprint hash for `foo()`: `01b83510cbb0619425304ea75d1bff3e`

## Add a comment to `foo()`
```python
def foo(a):
    # comment
    return a + 1

```
Fingerprint hash for `foo()`: `01b83510cbb0619425304ea75d1bff3e`

## Change formatting in `foo()`
```python
def foo(a):
    # comment

    return (a + \
            1)

```
Fingerprint hash for `foo()`: `01b83510cbb0619425304ea75d1bff3e`

## Change behavior of `foo()`
```python
def foo(a):
    return a + 2

```
Fingerprint hash for `foo()`: `9bb5cd485ab2eb457e2808a436b04c3f`
