"""
ESB Chatbot Utils Package
Contains utility functions and workflow components
"""

from .logging_config import setup_logging

__all__ = [
    'setup_logging'
]

import time
import functools
import logging

def retry_on_exception(
    exceptions, 
    tries=3, 
    delay=2, 
    backoff=2, 
    logger=None
):
    """
    Retry decorator for handling intermittent exceptions.
    Args:
        exceptions: Exception or tuple of exceptions to check.
        tries: Number of attempts.
        delay: Initial delay between retries (seconds).
        backoff: Backoff multiplier.
        logger: Optional logger to use.
    """
    def deco_retry(f):
        @functools.wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    msg = f"{f.__name__} failed with {e}, retrying in {mdelay}s... ({mtries-1} tries left)"
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)
        return f_retry
    return deco_retry
