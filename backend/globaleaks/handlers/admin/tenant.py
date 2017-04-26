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
from globaleaks.rest import requests, errors
from globaleaks.settings import GLSettings
from globaleaks.security import generateRandomKey
from globaleaks.utils.utility import log
from globaleaks.constants import ROOT_TENANT
from globaleaks.onion_services import db_configure_tor_hs


def serialize_tenant(tenant):
    d = {
        'id': tenant.id,
        'label': tenant.label,
        'active': tenant.active,
        'https_hostname': tenant.https_hostname,
        'onion_hostname': tenant.onion_hostname,
    }
    if tenant.wizard_token is not None:
        d['wizard_url'] = tenant.create_wizard_url()
    return d


def db_create_tenant(store, desc, appdata, require_token=True):
    tenant = Tenant(desc)

    if require_token:
        tenant.wizard_token = generateRandomKey(32)

    store.add(tenant)
    #TODO remove flush
    store.flush()

    config.db_create_config(store, tenant.id)

    EnabledLanguage.enable_language(store, tenant.id, u'en', appdata)

    # TODO talk with tor_ephem_hs to initialize an ephem HS
    if GLSettings.devel_mode:
        tenant.onion_address = 'do.something.onion'

    db_configure_tor_hs(store, tenant.id, GLSettings.bind_port)

    for t in [(u'logo', 'data/logo.png'),
              (u'favicon', 'data/favicon.ico')]:
        with open(os.path.join(GLSettings.client_path, t[1]), 'r') as file:
            data = base64.b64encode(file.read())
            models.config.NodeFactory(store, tenant.id).set_val(t[0], data)

    log.debug("Creating %s" % tenant)

    return tenant


@transact
def create_tenant(store, desc, appdata, *args, **kwargs):
    return serialize_tenant(db_create_tenant(store, desc, appdata, *args, **kwargs))


@transact
def get_tenant_list(store):
    return [serialize_tenant(tenant) for tenant in store.find(Tenant)]

@transact
def admin_update_tenant(store, tid, request):
    tenant = Tenant.db_get(store, id=tid)
    Tenant.update(tenant, request)


def root_tenant_only(f):
    """
    RequestHandler decorator that ensures that the function
    is called from the root tenant on a different tenant.
    """
    def wrapper(obj, *args, **kwargs):
        # The function must be called from the root tenant.
        if not obj.tstate.id == ROOT_TENANT:
            raise errors.ForbiddenOperation()

        # The function should be called on a different tenant
        # from the root tenant.
        if kwargs.get('tenant_id', None) == str(ROOT_TENANT):
            raise errors.ForbiddenOperation()

        return f(obj, *args, **kwargs)

    return wrapper


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

    @inlineCallbacks
    @root_tenant_only
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def post(self):
        """
        Create a new tenant
        """
        request = self.validate_message(self.request.body, requests.AdminTenantDesc)

        from globaleaks.db.appdata import load_appdata

        response = yield create_tenant(request, load_appdata(), require_token=True)

        yield self.app_state.refresh()

        self.set_status(201) # Created
        self.write(response)


class TenantInstance(BaseHandler):

    @inlineCallbacks
    @root_tenant_only
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def delete(self, tenant_id):
        """
        Delete the specified tenant.
        """
        tenant_id = int(tenant_id)
        yield Tenant.delete(id=tenant_id)
        yield self.app_state.refresh()

    @inlineCallbacks
    @root_tenant_only
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def put(self, tenant_id):
        request = self.validate_message(self.request.body,
                                        requests.AdminTenantUpdateDesc)

        tenant_id = int(tenant_id)
        yield admin_update_tenant(tenant_id, request)
        yield self.app_state.refresh()
