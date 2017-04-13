# -*- coding: UTF-8
#
#   tenant
#   *****
# Implementation of the Tenant handlers
#
import base64
import os
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.admin import files
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import Tenant, config
from globaleaks.models.l10n import EnabledLanguage
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log

from globaleaks.state import app_state


def serialize_tenant(tenant):
    return {
        'id': tenant.id,
        'label': tenant.label,
        'https_hostname': tenant.https_hostname,
        'onion_hostname': tenant.onion_hostname,
    }


def db_create_tenant(store, desc, appdata):
    tenant = Tenant(desc)
    store.add(tenant)

    #TODO remove flush
    store.flush()

    config.db_create_config(store, tenant.id)

    EnabledLanguage.enable_language(store, tenant.id, u'en', appdata)

    # TODO talk with tor_ephem_hs to initialize an ephem HS
    #if GLSettings.devel_mode:
    #  tenant.onion_address = 'do something crazy!!!!'

    for t in [(u'logo', 'data/logo.png'),
              (u'favicon', 'data/favicon.ico')]:
        with open(os.path.join(GLSettings.client_path, t[1]), 'r') as file:
            data = base64.b64encode(file.read())
            models.config.NodeFactory(store, tenant.id).set_val(t[0], data)

    log.debug("Creating %s" % tenant)

    return tenant


@transact
def create_tenant(store, desc, appdata):
    return serialize_tenant(db_create_tenant(store, desc, appdata))


@transact
def get_tenant_list(store):
    return [serialize_tenant(tenant) for tenant in store.find(Tenant)]


class TenantCollection(BaseHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Return the list of registered tenants
        """
        response = yield get_tenant_list()

        self.write(response)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Create a new tenant
        """
        request = self.validate_message(self.request.body, requests.AdminTenantDesc)

        from globaleaks.db.appdata import load_appdata

        response = yield create_tenant(request, load_appdata())

        yield app_state.refresh()

        self.set_status(201) # Created
        self.write(response)


class TenantInstance(BaseHandler):
    @inlineCallbacks
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def delete(self, tenant_id):
        """
        Delete the specified tenant.
        """
        tenant_id = int(tenant_id)
        if tenant_id == self.current_tenant:
            raise Exception('System will not delete the current tenant.')

        yield Tenant.delete(id=tenant_id)

        yield app_state.refresh()
