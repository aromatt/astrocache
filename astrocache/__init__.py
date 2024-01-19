import ast
import builtins
import functools
import hashlib
import importlib
import inspect
import os
import pickle
import shutil
import sys
import tempfile
import textwrap
import types

from contextlib import contextmanager
from pathlib import Path
from typing import Callable, NamedTuple, Optional, Set

CACHE_DIR = os.environ.get('ASTROCACHE_DIR', Path(tempfile.gettempdir()) / 'astrocache')
REFRESH = os.environ.get('ASTROCACHE_REFRESH')


class DereferenceError(Exception):
    pass


def _isbuiltin(func: Callable|str):
    if isinstance(func, str):
        return func in builtins.__dict__
    elif isinstance(func, Callable):
        return func.__module__ == 'builtins' or type(func) == types.BuiltinFunctionType
    else:
        return False


def _deref(name: str, context):
    """Find object called `name` in `context` and return it or raise an
    Exception.
    """
    obj = None
    if _isbuiltin(name):
        obj = getattr(builtins, name)
    else:
        if isinstance(context, Callable):
            if context.__name__ == name:
                # function is the context itself
                obj = context
            else:
                # function is in the context's scope
                obj = inspect.unwrap(context).__globals__.get(name)
        elif inspect.ismodule(context):
            # e.g. json.dumps
            obj = context.__dict__.get(name)
        else:
            # e.g. my_object.foo
            obj = getattr(context, name, None)
    if obj is None:
        raise DereferenceError(f"Unable to find '{name}' in context '{context}'")
    return obj

# TODO make sure @property is handled correctly
def _deref_attr(node: ast.Attribute, context):
    # find node for attribute
    attr_name = node.attr
    parent_name = node.value.id
    parent = None
    # An attribute may appear as foo.bar or self.bar
    if parent_name == 'self':
        parent = context.__self__
    else:
        parent = context.__globals__.get(parent_name)
    if parent is None:
        # see if parent is a module
        parent = sys.modules.get(parent_name)
    if parent is None:
        raise DereferenceError(f"Unable to find parent for '{node}'")
    # TODO what about getattr(foo, 'bar')()?
    return _deref(attr_name, parent)


def _ensure_func(obj: Callable) -> Callable:
    if not isinstance(obj, Callable):
        raise DereferenceError(f"Expected Callable, got {type(obj)}")
    return obj


def _node_for_func(func: Callable):
    if _isbuiltin(func):
        return None
    else:
        try:
            filename = Path(func.__code__.co_filename)
            src = textwrap.dedent(inspect.getsource(func))
            return ast.parse(src, filename=filename) if src else None
        except Exception as e:
            raise DereferenceError(
                f"Unable to find source for function {func.__module__}.{func.__name__}: {e}")


def _node_for_obj(obj: Callable):
    try:
        filename = Path(obj.__code__.co_filename)
        src = textwrap.dedent(inspect.getsource(obj))
        return ast.parse(src, filename=filename) if src else None
    except Exception as e:
        raise DereferenceError(f"Unable to find source for {obj}: {e}")


def _has_code(obj):
    return hasattr(obj, '__code__')


def _iter_func_nodes(node: ast.AST, context: Callable):
    """Visits all nodes in the provided AST, and yields all child nodes
    that are function definitions. This includes dereferencing functions
    from calls and expressions; their definitions are looked up in a __globals__
    dict, because they're not included in the AST of `node`. provided AST and
    need to be looked up.

    context: this tracks the scope in which to look up functions by name
    """

    # If node is a function definition, then yield it and update the context for
    # child nodes
    if type(node) == ast.FunctionDef:
        yield node
        context = _ensure_func(_deref(node.name, context))

    elif type(node) == ast.Attribute:
        attr = _deref_attr(node, context)
        if _has_code(attr):
            attr_node = _node_for_obj(attr)
            yield from _iter_func_nodes(attr_node, attr)

    # If node is a function call, find the function's definition
    # TODO may be able to remove this
    elif type(node) == ast.Call:
        # Normal function call
        if type(node.func) == ast.Name:
            # node.func will be handled on a recursive call while iterating over
            # child nodes
            pass
        # Method or module.function call
        elif type(node.func) == ast.Attribute:
            # TODO I think I can replace this with _deref_attr or remove it completely
            attr_name = node.func.attr
            parent_name = node.func.value.id
            parent = None
            # An attribute may appear as foo.bar or self.bar
            if parent_name == 'self':
                parent = context.__self__
            else:
                parent = context.__globals__.get(parent_name)
            if parent is None:
                # see if parent is a module
                parent = sys.modules.get(parent_name)
            if parent is None:
                raise DereferenceError(f"Unable to find parent for '{node}'")
            # TODO what about getattr(foo, 'bar')()?
            attr = _deref(attr_name, parent)
            if method_node := _node_for_func(attr):
                yield from _iter_func_nodes(method_node, attr)
            #yield from _iter_func_nodes(method_node, context)

    # A function name may appear as an ast.Name for function calls, argument
    # defaults, and expressions. In all cases, we need to dereference to find
    # the function definition.
    elif type(node) == ast.Name:
        # Don't need to dereference e.g. `foo` in `foo = 1`
        if not isinstance(node.ctx, ast.Store):
            obj = _deref(node.id, context)
            if isinstance(obj, Callable):
                if _isbuiltin(obj):
                    yield node
                else:
                    yield from _iter_func_nodes(_node_for_func(obj), context)

    # Recursively gather function definitions from child nodes
    for child_node in ast.iter_child_nodes(node):
        yield from _iter_func_nodes(child_node, context)


def _hash_prep(data):
    """Returns the information contained in `data`, restructured in a
    deterministic and hashable way."""
    if isinstance(data, set):
        prepped = tuple(sorted(map(_hash_prep, data)))
    elif isinstance(data, dict):
        prepped = tuple(sorted((k, _hash_prep(v)) for k, v in data.items()))
    elif isinstance(data, (tuple, list, map, filter)):
        prepped = tuple(map(_hash_prep, data))
    else:
        prepped = data
    # Include the type in order to differentiate between collection types
    # TODO: is this a good approach?
    return (type(data), prepped)


def _value_hash(obj) -> str:
    """Returns a deterministic hash representing the value of obj"""
    if isinstance(obj, Callable):
        # Using a function's fingerprint means that the cache key for `foo(bar)`
        # will be sensitive to the ASTs of both foo and bar.
        return _ast_fingerprint(obj)
    elif type(obj).__repr__ == object.__repr__:
        if type(obj).__hash__ == object.__hash__:
            raise ValueError(f"No deterministic __hash__ method for {obj}")
        else:
            return hash(obj)
    return _make_hash(_hash_prep(obj))


def _make_hash(*parts) -> str:
    # TODO using str is a problem, e.g. '<__main__.Foo object at 0x10337e9d0>'
    # is the str representation of a class without a __repr__ method.
    # instead of doing hash(str()) maybe it should be hash(pickle())
    return hashlib.md5(str(parts).encode()).hexdigest()


def _ast_fingerprint(func: Callable):
    """Returns a deterministic hash representing the implementation of func"""
    node = _node_for_func(func)
    digest = hashlib.md5()
    context = sys.modules.get(func.__module__)
    for func_node in _iter_func_nodes(node, context):
        digest.update(ast.dump(func_node).encode())
    return digest.hexdigest()


def _arg_fingerprint(args: list, kwargs: dict):
    return tuple(_value_hash(x) for x in args) + \
           tuple((k, _value_hash(v)) for k,v in kwargs.items())


@contextmanager
def _atomic_writer(path, mode='w'):
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


def _write_cache(path, data):
    with _atomic_writer(path, 'wb') as f:
        pickle.dump(data, f)
    return data


def _read_cache(path):
    with open(path, 'rb') as f:
        return pickle.load(f)


def _get_cache_id(func: Callable, args: list, kwargs: dict):
    return _make_hash(_ast_fingerprint(func), _arg_fingerprint(args, kwargs))


def clear_cache():
    if os.path.isdir(CACHE_DIR):
        shutil.rmtree(CACHE_DIR)


def cache(ignore_not_found: bool = False):
    """
    Decorator that adds a durable cache to the wrapped function.

    The cache key is generated based on the function's arguments, kwargs, and its
    implementation. The implementation is determined by its abstract syntax tree.
    The cache is stored in the directory specified by the ASTROCACHE_DIR
    environment variable or in a (deterministic) temporary directory if
    ASTROCACHE_DIR is not set.

    Parameters:
    ignore_not_found (Optional[bool]): Set to True to suppress error thrown when
        a function's source can't be found. Default: False (error is thrown).

    Returns:
    Callable: A wrapped function with caching applied.

    Usage:
    To use this decorator, simply apply it to a function definition:

    @astrocache.cache()
    def my_function(arg1, arg2):
        # Function implementation

    Note:
    - The cache is invalidated if the implementation of the function or any
      functions called by it. Referenced functions must be called directly,
      passed in as arguments, or defined inside the cached function in order for
      their implementations to be inspected. See README.md and test cases for
      more detail.
    - Changes in comments or formatting do not trigger cache invalidation.
    - Setting `ASTROCACHE_REFRESH` environment variable to a truthy value
      forces a cache refresh.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, no_cache=False, **kwargs):
            cache_id = _get_cache_id(func, args, kwargs)
            cache_path = os.path.join(CACHE_DIR, cache_id)
            if (not REFRESH) and (not no_cache) and os.path.isfile(cache_path):
                return _read_cache(cache_path)
            data = func(*args, **kwargs)
            if not no_cache:
                _write_cache(cache_path, data)
            return data
        return wrapper
    return decorator
