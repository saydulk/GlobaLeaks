# -*- coding: utf-8 -*-
import copy

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import user
from globaleaks.rest import errors
from globaleaks.tests import helpers


class TestContextsCollection(helpers.TestCollectionHandler):
    _handler = user.UsersCollection
    _instance_handler = user.UserInstance

    def forge_request_data(self):
        return copy.deepcopy(self.dummyReceiverUser_1)


class TestFieldInstance(helpers.TestInstanceHandler):
    _handler = user.UserInstance

    update_data = {
        'name': 'Mario Rossi'
    }

    def forge_request_data(self):
        return copy.deepcopy(self.dummyReciverUser_1)

    def get_existing_object(self):
        return self.dummyReceiverUser_1

    @inlineCallbacks
    def test_delete_first_admin_user_should_fail(self):
        handler = self.request(role=self.user_role)
        yield self.assertFailure(handler.delete(self.dummyAdminUser['id']),
                                 errors.UserNotDeletable)
