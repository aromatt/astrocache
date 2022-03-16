import ast
import builtins
import functools
import hashlib
import inspect
import os
import pickle
import shutil
import tempfile
import textwrap

from contextlib import contextmanager
from pathlib import Path
from typing import Callable, NamedTuple, Optional

CACHE_DIR = os.environ.get('FUNCACHE_DIR', Path(tempfile.gettempdir()) / 'funcache')
REFRESH = os.environ.get('FUNCACHE_REFRESH')


class Function(NamedTuple):
    """Function is a metadata record for a function."""
    function: Callable
    name: str
    source: Optional[str]
    ast: Optional[ast.AST]
    module_name: Optional[str]
    filename: Optional[Path]

    @classmethod
    def from_func(cls, func: Callable, strict: bool = False):
        if hasattr(builtins, func.__name__):
            filename = '<builtin>'
            src = None
        else:
            try:
                filename = Path(func.__code__.co_filename)
                src = textwrap.dedent(inspect.getsource(func))
            except:
                if not strict:
                    filename = '<unknown>'
                    src = None
                else:
                    raise ValueError(f"Unable to find source for function {func.__module__}.{func.__name__}")
        node = ast.parse(src, filename=filename) if src else None
        return cls(function=func,
                   name=func.__name__,
                   source=src,
                   ast=node,
                   module_name=func.__module__,
                   filename=filename)

    @classmethod
    def from_call(cls, caller, node: ast.Call, strict: bool = False):
        """Given the provided ast.Call `node` within Function `caller`, return
        the called function as a Function or None"""
        func = None
        func_obj = node.func
        # Normal function call?
        if type(func_obj) == ast.Name:
            func_name = func_obj.id
            if hasattr(builtins, func_name):
                func = getattr(builtins, func_name)
            else:
                func = caller.function.__globals__.get(func_name)
        # Method call?
        elif type(func_obj) == ast.Attribute:
            if type(func_obj.value) == ast.Name:
                parent_name = func_obj.value.id
                func_name = func_obj.attr
                if parent_name == 'self':
                    parent = caller.function.__self__
                else:
                    parent = caller.function.__globals__.get(parent_name)
                if parent:
                    func = getattr(parent, func_name)
        if func:
            return Function.from_func(func, strict=strict)
        elif strict:
            raise ValueError(f"Unable to find function from {ast.dump(node)}")

    def fingerprint(self, root: Optional[str] = None, strict: bool = False):
        """Return the implementation fingerprint for this Function. Provide
        `root` to limit the depth of introspection to a particular directory."""
        if root is None:
            root = os.path.dirname(self.filename)

        def _get_func_defs(func: Function, node: ast.AST):
            defs = {}
            if node is None or not func.filename.is_relative_to(root):
                return defs
            def_hash = hashlib.md5(ast.dump(func.ast).encode()).hexdigest()
            defs[f'{func.module_name}.{func.name}'] = def_hash
            # Recurse into child nodes.
            for child_node in ast.iter_child_nodes(node):
                # To recurse into a call; we must find the called function
                if type(child_node) == ast.Call:
                    called_func = Function.from_call(func, child_node, strict=strict)
                    if called_func:
                        defs.update(_get_func_defs(called_func, called_func.ast))
                    elif strict:
                        raise ValueError(f"Unable to find function from {ast.dump(node)}")
                else:
                    defs.update(_get_func_defs(func, child_node))
            return defs

        defs = _get_func_defs(self, self.ast)
        parts = sorted((k,v) for k,v in defs.items())
        return parts

    def __hash__(self):
        return self.fingerprint(strict=True)


def _value_hash(obj, strict: bool = False):
    """Returns a deterministic hash representing the value of obj if possible;
    otherwise returns None, or if `strict` then raises an exception."""
    # Support deterministic hashes for functions as args!
    if isinstance(obj, Callable):
        return Function.from_func(obj, strict=strict).fingerprint()
    # Do not use __hash__ if it was inherited from `object`
    elif type(obj).__hash__ != object.__hash__:
        try:
            return hash(obj)
        except Exception as e:
            if strict:
                raise ValueError(f"Unable to hash {type(obj)} {obj}: {e}")
    else:
        if strict:
            raise ValueError(f"Unable to hash {type(obj)} {obj}: {e}")


def make_hash(*parts):
    return hashlib.md5(str(parts).encode()).hexdigest()


def func_fingerprint(func: Callable, root: Optional[str] = None, strict: bool = False):
    """Returns a hash that changes when the implementation of func changes."""
    return Function.from_func(func, strict=strict).fingerprint(root=root, strict=strict)


def arg_fingerprint(args: list, kwargs: dict, strict: bool = False):
    return [
        *[_value_hash(x, strict=strict) for x in args],
        *[(k, _value_hash(v)) for k,v in kwargs.items()],
    ]


@contextmanager
def atomic_writer(path, mode='w'):
    """Yields temp file and moves it to specified path on context exit. Creates
    destination directory if it doesn't already exist."""
    if 'a' in mode:
        raise ValueError('Cannot append atomically')
    parent = os.path.dirname(path)
    os.makedirs(parent, exist_ok=True)
    f = tempfile.NamedTemporaryFile(mode=mode, dir=parent, delete=False)
    try:
        try:
            yield f
        finally:
            f.close()
        os.rename(f.name, path)
    except Exception:
        os.remove(f.name)
        raise


def atomic_write(path, content, mode='w'):
    """Write content to temp file and move to specified path"""
    with atomic_writer(path, mode=mode) as f:
        f.write(content)


def _write_cache(path, data):
    with atomic_writer(path, 'wb') as f:
        pickle.dump(data, f)
    return data


def _read_cache(path):
    with open(path, 'rb') as f:
        return pickle.load(f)


def clear_cache():
    if os.path.isdir(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)


def get_cache_id(func: Callable, args: list, kwargs: dict,
        root: Optional[str] = None, strict: bool = False):
    return make_hash(func_fingerprint(func, root=root, strict=strict),
                     arg_fingerprint(args, kwargs, strict=strict))


def cache(root: Optional[str] = None, strict: bool = False):
    """
    cache() is a decorator which adds a durable cache to the wrapped function.
    The cache key is a combination of the function's args, kwargs, and implementation.
    Function implementation is determined recursively, but inspection is limited to
    source files within `root`, which is configurable via the kwarg, and defaults to
    the directory containing the function's module.

    Use like so:
        @funcache.cache()
        def my_function(foo, bar):
            return foo + bar

    Options to @funcache.cache():
      - root: Attempt to inspect source code within this directory. Default is
              parent of function's module.
      - strict: If any arguments cannot be deterministically hashed, or any functions
                cannot be found, raise an exception instead of skipping over them.

    When calling a cached function, you may set `no_cache=True` to prevent use of
    the cache for that invocation.

    Changing a function's implementation invalidates the cache... to an extent.

    These things count as part of a function's implementation:
      - The function's own expressions
      - Function definitions within the cached function
      - Class definitions within the cached function
      - Definitions of all functions called by the cached function
      - Definitions of functions received as parameters by the cached function

    And these don't:
      - Definitions of functions assigned to variables, e.g. `foo = some_function`
      - Definitions of functions used as arguments, e.g. `bar(some_function)`

    However, if you want a referenced function's implementation to be included in
    your cache key, you can just accept it as a parameter.

    Example:
        @funcache.cache()
        def my_func(foo, other_func):
            something(other_func)
            return foo + 1

    Here, even though my_func never calls other_func, other_func's implementation
    will still be included in the cache key for my_func.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, no_cache=False, **kwargs):
            cache_id = get_cache_id(func, args, kwargs, root=root, strict=strict)
            cache_path = os.path.join(CACHE_DIR, cache_id)
            if (not REFRESH) and (not no_cache) and os.path.isfile(cache_path):
                return _read_cache(cache_path)
            data = func(*args, **kwargs)
            if not no_cache:
                _write_cache(cache_path, data)
            return data
        return wrapper
    return decorator
