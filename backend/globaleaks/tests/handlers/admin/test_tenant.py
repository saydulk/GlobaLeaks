# -*- coding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks

from globaleaks.db.appdata import load_appdata
from globaleaks.handlers.admin import tenant
from globaleaks.tests import helpers


class TestTenantCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = tenant.TenantCollection

    @inlineCallbacks
    def test_get(self):
        for i in range(3):
            yield tenant.create_tenant({'label': 'tenant-%i' % i}, load_appdata())

        handler = self.request(role='admin')
        yield handler.get()

        self.assertEqual(len(self.responses[0]), 3+2)

    @inlineCallbacks
    def test_post_new_tenant(self):
        handler = self.request({'label': 'tenant-xxx'}, role='admin')
        yield handler.post()


class TestTenantnstance(helpers.TestHandlerWithPopulatedDB):
    _handler = tenant.TenantInstance

    @inlineCallbacks
    def test_delete(self):
        tenant_desc = yield tenant.create_tenant({'label': 'tenant-xxx'}, load_appdata())

        handler = self.request(role='admin')
        yield handler.delete(tenant_desc['id'])
