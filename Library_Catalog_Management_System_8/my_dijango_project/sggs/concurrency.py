import functools
from django.db import transaction, models
from django.db.utils import OperationalError, IntegrityError


MAX_RETRIES = 3


def retry_on_conflict(max_retries=None):
    if max_retries is None:
        max_retries = MAX_RETRIES

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    with transaction.atomic():
                        result = func(*args, **kwargs)
                        return result
                except (OperationalError, IntegrityError) as e:
                    last_exception = e
                    error_str = str(e).lower()
                    if 'deadlock' in error_str or 'version' in error_str:
                        if attempt < max_retries - 1:
                            continue
                    raise
            raise last_exception

        @functools.wraps(func)
        def async_wrapper(*args, **kwargs):
            return wrapper(*args, **kwargs)

        return async_wrapper

    return decorator