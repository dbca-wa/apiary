# your_app/request_cache.py
from contextvars import ContextVar
from functools import wraps

# 1. Thread-safe/Async-safe context variable to hold the dictionary
_request_cache: ContextVar[dict] = ContextVar("_request_cache")


def get_request_cache():
    """Retrieve the dictionary for the current request."""
    try:
        return _request_cache.get()
    except LookupError:
        # If accessed outside a web request (e.g., in a Celery task or management command)
        return None


# 2. The Decorator
def per_request_cache(func):
    """Caches the result of a function call only for the duration of the current HTTP request."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        cache = get_request_cache()

        # If outside the request lifecycle, run the function normally without caching
        if cache is None:
            return func(*args, **kwargs)

        # Create a unique cache key based on function name and its arguments
        cache_key = (func.__qualname__, args, frozenset(kwargs.items()))

        if cache_key not in cache:
            cache[cache_key] = func(*args, **kwargs)

        return cache[cache_key]

    return wrapper
