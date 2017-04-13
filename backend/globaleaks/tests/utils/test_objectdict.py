# -*- coding: utf-8 -*-

from globaleaks.tests import helpers
from globaleaks.utils.objectdict import ObjectDict


class TestTempDict(helpers.TestGL):
    def test_object_dict(self):
        od = ObjectDict()
        self.assertRaises(AttributeError, getattr, od, "something")
        od["foo"] = "bar"
        self.assertEqual(od['foo'], "bar")
        self.assertEqual(od.foo, "bar")
        od.rah = "meow"
        self.assertEqual(od['rah'], "meow")
