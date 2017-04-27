# -*- coding: utf-8 -*-
import copy

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin import step
from globaleaks.tests import helpers


class TestStepCollection(helpers.TestCollectionHandler):
        _handler = step.StepCollection
        _instance_handler = step.StepInstance

        def forge_request_data(self):
            req = helpers.get_dummy_step()
            req['questionnaire_id'] = self.dummyContext['questionnaire_id']
            return req

        def test_get(self):
            pass


class TestStepInstance(helpers.TestInstanceHandler):
        _handler = step.StepInstance

        update_data = {
            'tip_timetolive': 666
        }

        def forge_request_data(self):
            req = helpers.get_dummy_step()
            req['questionnaire_id'] = self.dummyContext['questionnaire_id']
            return req

        def get_existing_object(self):
            return self.dummyQuestionnaire['steps'][1]
