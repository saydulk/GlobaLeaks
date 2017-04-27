# -*- encoding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers import admin, rtip
from globaleaks.state import app_state
from globaleaks.jobs.delivery_sched import DeliverySchedule
from globaleaks.tests import helpers
from globaleaks.utils.templating import Templating, supported_template_types


class notifTemplateTest(helpers.TestGLWithPopulatedDB):
    @inlineCallbacks
    def test_keywords_conversion(self):
        yield self.perform_full_submission_actions()
        yield DeliverySchedule().run()

        data = {}
        data['type'] = 'tip'
        data['receiver'] = self.dummyReceiver_1
        data['context'] = self.dummyContext
        data['notification'] = yield admin.notification.get_notification(app_state.root_id, 'en')
        data['node'] = yield admin.node.admin_serialize_node(app_state.root_id, 'en')

        if self.dummyRTips[0]['receiver_id'] == self.dummyReceiver_1['id']:
            tip_id = self.dummyRTips[0]['id']
        else:
            tip_id = self.dummyRTips[1]['id']

        data['tip'] = yield rtip.get_rtip(self.dummyReceiver_1['id'], tip_id, 'en')

        data['comment'] = data['tip']['comments'][0]
        data['message'] = data['tip']['messages'][0]

        files = yield rtip.receiver_get_rfile_list(data['tip']['id'])
        data['file'] = files[0]

        for key in ['tip', 'comment', 'message', 'file']:
            data['type'] = key
            template = ''.join(supported_template_types[key].keyword_list)
            Templating().format_template(template, data)
