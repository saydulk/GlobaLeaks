# -*- coding: utf-8 -*-
import copy

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import receiver
from globaleaks.rest import errors
from globaleaks.tests import helpers
from globaleaks.utils.utility import uuid4


class TestReceiverCollection(helpers.TestCollectionHandler):
    _handler = receiver.ReceiversCollection
    _instance_handler = receiver.ReceiverInstance

    def forge_request_data(self):
        return copy.deepcopy(self.dummyReceiver_1)

    def test_post(self):
        pass


class TestFieldInstance(helpers.TestInstanceHandler):
    _handler = receiver.ReceiverInstance

    update_data = {
        'tip_timetolive': 666
    }

    def forge_request_data(self):
        return copy.deepcopy(self.dummyReceiver_1)

    def get_existing_object(self):
        return self.dummyReceiver_1

    @inlineCallbacks
    def test_put_invalid_context_id(self):
        self.dummyReceiver_1['contexts'] = [unicode(uuid4())]

        handler = self.request(self.dummyReceiver_1, role='admin')

        yield self.assertFailure(handler.put(self.dummyReceiver_1['id']),
                                 errors.ModelNotFound)

    def test_delete(self):
        pass
