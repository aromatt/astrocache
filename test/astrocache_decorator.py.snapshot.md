
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
ValueError: Unable to find function from Call(func=Name(id='_repr', ctx=Load()), args=[Name(id='o', ctx=Load())], keywords=[])
```
```python
>>> foo(1, 2)
ValueError: Unable to find function from Call(func=Name(id='_repr', ctx=Load()), args=[Name(id='o', ctx=Load())], keywords=[])
```

## Call `foo()` with different args
```python
>>> foo(1, 3)
ValueError: Unable to find function from Call(func=Name(id='_repr', ctx=Load()), args=[Name(id='o', ctx=Load())], keywords=[])
```

## Change implementation of `scale()`
```python
def scale(x):
    print('scale() called')
    return x * 3

```
```python
>>> foo(1, 2)
ValueError: Unable to find function from Call(func=Name(id='_repr', ctx=Load()), args=[Name(id='o', ctx=Load())], keywords=[])
```
