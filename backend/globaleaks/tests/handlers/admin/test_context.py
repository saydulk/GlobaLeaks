# -*- coding: utf-8 -*-
import copy

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import context
from globaleaks.tests import helpers


class TestContextsCollection(helpers.TestCollectionHandler):
    _handler = context.ContextsCollection
    _instance_handler = context.ContextInstance

    def forge_request_data(self):
        return copy.deepcopy(self.dummyContext)


class TestContextInstance(helpers.TestInstanceHandler):
    _handler = context.ContextInstance

    update_data = {
        'tip_timetolive': 666
    }

    def forge_request_data(self):
        return copy.deepcopy(self.dummyContext)

    def get_existing_object(self):
        return self.dummyContext
