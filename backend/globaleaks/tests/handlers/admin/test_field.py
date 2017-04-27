# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import admin
from globaleaks.tests import helpers


class TestFieldCreate(helpers.TestCreateHandler):
        _handler = admin.field.FieldCollection

        def forge_request_data(self):
            req = helpers.get_dummy_field()
            req['instance'] = 'instance'
            req['step_id'] = self.dummyQuestionnaire['steps'][0]['id']
            return req

        @inlineCallbacks
        def test_post_create_from_template(self):
            """
            Attempt to create a new field from template via post request
            """
            req = self.forge_request_data()
            req['instance'] = 'template'
            handler = self.request(req, role=self.user_role)
            yield handler.post()

            req = self.forge_request_data()
            req['reference_id'] = self.responses[0]['id']
            handler = self.request(req, role=self.user_role)
            yield handler.post()


class TestFieldInstance(helpers.TestInstanceHandler):
        _handler = admin.field.FieldInstance

        update_data = {
            'x': 666
        }

        def forge_request_data(self):
            req = helpers.get_dummy_field()
            req['instance'] = 'instance'
            req['step_id'] = self.dummyQuestionnaire['steps'][0]['id']
            return req

        def get_existing_object(self):
            return self.dummyQuestionnaire['steps'][0]['children'][0]


class TestFieldTemplateInstance(TestFieldInstance):
        _handler = admin.field.FieldTemplateInstance

        def forge_request_data(self):
            req = helpers.get_dummy_field()
            req['instance'] = 'template'
            return req


class TestFieldTemplatesCollection(helpers.TestCollectionHandler):
        _handler = admin.field.FieldTemplatesCollection
        _instance_handler = admin.field.FieldTemplateInstance

        def forge_request_data(self):
            req = helpers.get_dummy_field()
            req['instance'] = 'template'
            return req
