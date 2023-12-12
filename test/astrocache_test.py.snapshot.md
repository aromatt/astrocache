

#######################################
# Function implementation fingerprint #
#######################################

# Using the following definitions:
```
def three(h):
    return json.dumps(h)

def two(c):
    # Call a function in a different module
    return foo.three({'a': c + 1})

def make_thing(a):
    return a + 1

def nested_function_def():
    def blah(x):
        return x + 1

def nested_class_def():
    class Foo:
        def __init__(self, a):
            self.thing = make_thing(a)
    return Foo

def fn_to_assign(x):
    return x + 1

def fn_to_pass(x):
    return x * 1

def one(a, b):
    # Call a function that contains a function definition
    nested_function_def()
    # Call a function that contains a class definition
    nested_class_def()
    # Assign a function to a variable, but don't call it
    fn = fn_to_assign
    # Pass a function as an argument, but don't call it
    think_about_function(fn_to_pass)
    return two(a + b)

```

# What is the fingerprint of one()?
Fingerprint hash for one(): cc6adb6c3b1f31ea33351c3410b78b9b

# Adding a comment to make_thing()
Fingerprint hash for one(): cc6adb6c3b1f31ea33351c3410b78b9b

# Change formatting in make_thing()
Fingerprint hash for one(): cc6adb6c3b1f31ea33351c3410b78b9b

# Change behavior of make_thing()
Fingerprint hash for one(): fee307a11892a7da3c4aefa9411c0f5f

# Change implementation of fn_to_assign(). TODO support this! fingerprint should change
Fingerprint hash for one(): fee307a11892a7da3c4aefa9411c0f5f

# Change implementation of fn_to_pass(). TODO support this! fingerprint should change
Fingerprint hash for one(): fee307a11892a7da3c4aefa9411c0f5f


#######################
# @astrocache.cache() #
#######################

# Using the following definition:
```
@astrocache.cache()
def cached_func(x, **kwargs):
    print("EXECUTED")
    return one(x, 1)

```

# Testing basic memoization
>>> cached_func(100)
EXECUTED
{"a": 102}
>>> cached_func(100)
{"a": 102}

# Change behavior of make_thing(100)
>>> cached_func(100)
EXECUTED
{"a": 102}
>>> cached_func(100)
{"a": 102}

# Different args
>>> cached_func(999)
EXECUTED
{"a": 1001}
>>> cached_func(999)
{"a": 1001}

# Adding kwarg
>>> cached_func(999, foo=True)
EXECUTED
{"a": 1001}
>>> cached_func(999, foo=True)
{"a": 1001}

# Using no_cache
>>> cached_func(999, foo=True, no_cache=True)
EXECUTED
{"a": 1001}

# Are functions passed into cached function included in fingerprint?
>>> cached_func(100, func=make_thing)
EXECUTED
{"a": 102}
>>> cached_func(100, func=make_thing)
{"a": 102}

# Change behavior of make_thing()
>>> cached_func(100, func=make_thing)
EXECUTED
{"a": 102}

# Making sure cache_id is deterministic across processes when args include functions
_get_cache_id(make_thing, [make_thing], dict(fn=make_thing))
24fc188cd2c6ca5cf417ce102eddb8c4


##############
# Exceptions #
##############

# Using the following definition:
```
@astrocache.cache(root='/')
def root_fn(a):
    return json.dumps(a)

```

# Calling a cached function with root='/'
>>> root_fn(1)
ValueError: Unable to find source for function _json.encode_basestring_ascii

# Can args include lists?
>>> _get_cache_id('make_thing', [[1]], {})
f320090f7e42ee5ab0de0c1b10b9e1ff

# Can args include dicts?
>>> _get_cache_id('make_thing', [{1: 2}], {})
8a3d8b0356e1550140a6b6d67e087600

# Can args include sets?
>>> _get_cache_id('make_thing', [{1}], {})
c4f95f3677455495b226e6705afedd6a

# Can args include None?
>>> _get_cache_id('make_thing', [None], {})
a7ae9dc1c122a61ac22e4abdadd83ad4

# Using the following definition:
```
class Foo:
    def __init__(self, a): self.a = a
    def __repr__(self): return f'Foo({self.a})'

```

# Can args include classes?
>>> _get_cache_id('make_thing', ['Foo'], {})
ValueError: Unable to find source for function __main__.Foo

# Can args include instances of hashable user-defined classes?
>>> _get_cache_id('make_thing', [Foo(1)], {})
2258ceae8daef9450aa2e4346001cc09
