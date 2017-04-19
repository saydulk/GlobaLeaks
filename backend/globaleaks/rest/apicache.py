# -*- coding: UTF-8

from twisted.internet.defer import inlineCallbacks, returnValue, Deferred


class GLApiCache(object):
    _cache = dict()

    @classmethod
    @inlineCallbacks
    def get(cls, tid, resource, language, function, *args, **kwargs):
        """
        Get a resource from cache.
        The function is written to be run in main twisted thread,
        guarantee of no concurrency.
        """
        if tid not in cls._cache:
            cls._cache[tid] = {}

        if resource not in cls._cache[tid]:
            cls._cache[tid][resource] = {}

        if language not in cls._cache[tid][resource]:
            deferred = Deferred()
            cls._cache[tid][resource][language] = deferred
            value = yield function(*args, **kwargs)
            cls._cache[tid][resource][language] = value
            deferred.callback(None)
        else:
            if isinstance(cls._cache[tid][resource][language], Deferred):
                yield cls._cache[tid][resource][language]

        returnValue(cls._cache[tid][resource][language])


    @classmethod
    def invalidate(cls, tid=None, resource=None, language=None):
        """
        Invalidate cache.
        The function is written to be run in main twisted thread,
        guarantee of no concurrency.
        """
        if language is not None:
            del cls._cache[tid][resource][language]

        elif resource is not None:
            del cls._cache[tid][resource]

        elif tid is not None:
            del cls._cache[tid]

        else:
            cls._cache.clear()
