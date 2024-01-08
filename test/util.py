import types
from typing import Callable

import astrocache


# Markdown generation helpers

def h1(msg): print(f"\n# {msg}")
def h2(msg): print(f"\n## {msg}")
def h3(msg): print(f"\n### {msg}")
def text_block(text): print(f"{text}\n")

def code_block_start():
    print("```python")

def code_block_end():
    print("```")

def code_block(code):
    code_block_start()
    print(code)
    code_block_end()

def get_fn_name(fn):
    """Returns the name of `fn` as a deterministic string"""
    if hasattr(fn, '__self__'):
        owner = fn.__self__
        if hasattr(owner, '__name__'):
            owner_name = owner.__name__
        else:
            owner_name = str(owner)
        return f"{owner_name}.{fn.__name__}"
    else:
        return fn.__qualname__


def sanitize(data):
    if isinstance(data, (types.GeneratorType, list, map, filter, tuple)):
        return [sanitize(x) for x in data]
    elif isinstance(data, dict):
        return {k: sanitize(v) for k, v in data.items()}
    elif isinstance(data, Callable):
        return get_fn_name(data)
    elif type(data).__repr__ == object.__repr__:
        # Need to support classes without __repr__ implementations in order to
        # test _make_hash() properly
        return f'<{type(data).__name__} instance>'
    else:
        return data


def get_param_str(args, kwargs):
    return ', '.join([*map(repr, sanitize(args)),
                    *[f"{k}={v}" for k,v in sanitize(kwargs).items()]])


def invoke(fn, *args, **kwargs):
    """Call `fn` with provided args and kwargs, printing the invocation and its
    result"""
    name = get_fn_name(fn)
    param_str = get_param_str(args, kwargs)
    code_block_start()
    print(f">>> {name}({param_str})")
    try:
        result = fn(*args, **kwargs)
    except Exception as e:
        result = f"{type(e).__name__}: {e}"
    print(result)
    code_block_end()


def func_fingerprint_hash(func, **kwargs):
    return astrocache._make_hash(astrocache._func_fingerprint(func, **kwargs))


def print_fingerprint(func):
    print(f"Fingerprint hash for `{func.__name__}()`: `{func_fingerprint_hash(func)}`")
