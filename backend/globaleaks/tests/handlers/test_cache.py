# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact
from globaleaks.rest.apicache import GLApiCache
from globaleaks.tests import helpers


class TestGLApiCache(helpers.TestGL):
    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGL.setUp(self)

        GLApiCache.invalidate()

    @staticmethod
    @transact
    def mario(store, arg1, arg2, arg3):
        return arg1 + " " + arg2 + " " + arg3

    @inlineCallbacks
    def test_cache(self):
        self.assertTrue(1 not in GLApiCache._cache)
        self.assertTrue(2 not in GLApiCache._cache)

        pdp_1_it = yield GLApiCache.get(1, "passante_di_professione", "it", self.mario, "come", "una", "catapulta!")
        pdp_1_en = yield GLApiCache.get(1, "passante_di_professione", "en", self.mario, "like", "a", "catapult!")
        pdp_2_en = yield GLApiCache.get(2, "passante_di_professione", "en", self.mario, "like", "a", "catapult!")

        self.assertEqual(pdp_1_it, "come una catapulta!")
        self.assertEqual(pdp_1_en, "like a catapult!")
        self.assertEqual(pdp_2_en, "like a catapult!")

        yield GLApiCache.invalidate(1, "passante_di_professione", 'it')
        self.assertTrue('it' not in GLApiCache._cache[1]['passante_di_professione'])
        yield GLApiCache.invalidate(1, "passante_di_professione")
        self.assertTrue('passante_di_professione' not in GLApiCache._cache[1])
        yield GLApiCache.invalidate(1)
        self.assertTrue(1 not in GLApiCache._cache)

        pdp_2_en = yield GLApiCache.get(2, "passante_di_professione", "en", self.mario, "a", "b", "c")

        self.assertEqual(pdp_2_en, "like a catapult!")

        yield GLApiCache.invalidate()

        pdp_2_en = yield GLApiCache.get(2, "passante_di_professione", "en", self.mario, "a", "b", "c")

        self.assertEqual(pdp_2_en, "a b c")
