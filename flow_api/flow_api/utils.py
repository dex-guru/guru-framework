import asyncio
from asyncio import AbstractEventLoop
from hashlib import md5

from aiocache import Cache
from aiocache.serializers import PickleSerializer
from fastapi import Request

from async_fastapi_jwt_auth import AuthJWT
from async_fastapi_jwt_auth.auth_jwt import AuthJWTBearer
from fa_admin.settings import CACHE, REDIS_PORT, REDIS_HOST, REDIS_DATABASE


def make_update_dict(**kwargs):
    return {k: v for k, v in kwargs.items() if v is not None}


CACHE_TTL_30s = 30
CACHE_TTL_5m = 300
CACHE_TTL_15m = 900
CACHE_TTL_30m = 1800

IGNORE_ARG_TYPES = (AbstractEventLoop, Request, AuthJWT, AuthJWTBearer)


def key_from_filtered_args(func, *args, **kwargs):
    """Builds a cache key. Ignores event loop and request arguments."""
    return _key_from_filtered_args(func, args, kwargs, noself=False)


def key_from_filtered_args_noself(func, *args, **kwargs):
    """Builds a cache key. Ignores event loop, request and `self` arguments."""
    return _key_from_filtered_args(func, args, kwargs, noself=True)


def _key_from_filtered_args(func, args, kwargs, noself):
    filtered_args = _filter_args(args)
    if noself and filtered_args:  # ignore first argument
        filtered_args = filtered_args[1:]
    filtered_args = tuple(filtered_args)
    filtered_kwargs = _filter_kwargs(kwargs)
    ordered_kwargs = sorted(filtered_kwargs.items())
    key = (
        (func.__module__ or "")
        + func.__name__
        + str(filtered_args)
        + str(ordered_kwargs)
    )
    md5_hash = md5(key.encode()).digest()
    return md5_hash


def _filter_args(args):
    if args is None:
        return []
    return [arg for arg in args if not isinstance(arg, IGNORE_ARG_TYPES)]


def _filter_kwargs(kwargs):
    if kwargs is None:
        return {}
    return {k: v for (k, v) in kwargs.items() if not isinstance(v, IGNORE_ARG_TYPES)}


def skip_cache_func(obj):
    if not obj:
        return True
    if isinstance(obj, dict):
        return obj.get("error") or obj.get("errors") or obj.get("result", "") is None
    if isinstance(obj, (list, tuple)):
        return any(skip_cache_func(o) for o in obj)
    return False


if CACHE == "redis":
    CACHE_CONFIG = {
        "cache": Cache.REDIS,
        "endpoint": REDIS_HOST,
        "port": REDIS_PORT,
        "serializer": PickleSerializer(),
        "db": REDIS_DATABASE,
        "key_builder": key_from_filtered_args,
        # "skip_cache_func": skip_cache_func,
    }
else:
    CACHE_CONFIG = {
        "cache": Cache.MEMORY,
        "serializer": PickleSerializer(),
        "key_builder": key_from_filtered_args,
        # "skip_cache_func": skip_cache_func,
    }


def create_background_task(all_tasks: set, coro):
    task = asyncio.create_task(coro)
    all_tasks.add(task)
    task.add_done_callback(all_tasks.discard)
