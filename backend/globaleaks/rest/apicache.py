from twisted.internet.defer import inlineCallbacks, returnValue


class GLApiCache(object):
    _cache = dict()

    @classmethod
    @inlineCallbacks
    def get(cls, tid, resource, language, function, *args, **kwargs):
        """
        Get a resource from cache.
        The function is written to be run in main twisted thread,
        guaranee of no concurrency.
        """
        try:
            returnValue(cls._cache[tid][resource][language])
        except KeyError:
            value = yield function(*args, **kwargs)

            if tid not in cls._cache:
                cls._cache[tid] = {}

            if resource not in cls._cache[tid]:
                cls._cache[tid][resource] = {}

            if language not in cls._cache[tid][resource]:
                cls._cache[tid][resource][language] = value

            returnValue(cls._cache[tid][resource][language])

    @classmethod
    def invalidate(cls, tid=None, resource=None, language=None):
        """
        Invalidate cache.
        The function is written to be run in main twisted thread,
        guaranee of no concurrency.
        """
        try:
            if language is not None and resource is not None and tid is not None:
                del cls._cache[tid][resource][language]

            elif resource is not None and tid is not None:
                del cls._cache[tid][resource]

            elif tid is not None:
                del cls._cache[tid]

            else:
                cls._cache.clear()
        except KeyError:
            pass
