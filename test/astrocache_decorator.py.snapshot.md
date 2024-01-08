
## Definitions
```python
def scale(x):
    print('scale() called')
    return x * 2

```
```python
@astrocache.cache()
def foo(a, b):
    data = {'value': scale(a) + b}
    # Include a standard library function in the implementation
    return json.dumps(data)

```

## Call `foo()` twice with the same args
```python
>>> foo(1, 2)
scale() called
{"value": 4}
```
```python
>>> foo(1, 2)
{"value": 4}
```

## Call `foo()` with different args
```python
>>> foo(1, 3)
scale() called
{"value": 5}
```

## Change implementation of `scale()`
```python
def scale(x):
    print('scale() called')
    return x * 3

```
```python
>>> foo(1, 2)
scale() called
{"value": 5}
```
