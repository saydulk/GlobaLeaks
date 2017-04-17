# -*- coding: UTF-8
#
# wizard
from storm.expr import And
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.admin.context import db_create_context
from globaleaks.handlers.admin.node import  set_enabled_languages
from globaleaks.handlers.admin.receiver import db_create_receiver
from globaleaks.handlers.admin.user import db_create_admin_user
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.public import serialize_node
from globaleaks.models.config import NodeFactory
from globaleaks.models.l10n import EnabledLanguage, NodeL10NFactory
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import log, datetime_null


@transact
def wizard(store, tid, request, language):
    node = NodeFactory(store, tid)

    if node.get_val('wizard_done'):
        # TODO report as anomaly
        log.err("DANGER: Wizard already initialized!")
        raise errors.ForbiddenOperation

    node._query_group()

    nn = unicode(request['node']['name'])
    node.set_val('name', nn)
    node.set_val('default_language', language)
    node.set_val('wizard_done', True)

    node_l10n = NodeL10NFactory(store, tid)

    node_l10n.set_val('description', language, nn)
    node_l10n.set_val('header_title_homepage', language, nn)
    node_l10n.set_val('presentation', language, nn)

    context = db_create_context(store, tid, request['context'], language)

    if language != u'en':
        set_enabled_languages(store, tid, language, [language])

    request['receiver']['contexts'] = [context.id]
    request['receiver']['language'] = language
    db_create_receiver(store, tid, request['receiver'], language)

    admin_dict = {
        'password': request['admin']['password'],
        'role': u'admin',
        'state': u'enabled',
        'deletable': False,
        'name': u'Admin',
        'public_name': u'Admin',
        'description': u'',
        'mail_address': request['admin']['mail_address'],
        'language': language,
        'password_change_needed': False,
        'pgp_key_remove': False,
        'pgp_key_fingerprint': '',
        'pgp_key_public': '',
        'pgp_key_expiration': datetime_null()
    }

    db_create_admin_user(store, tid, admin_dict, language)


class Wizard(BaseHandler):
    """
    Setup Wizard handler
    """
    @BaseHandler.unauthenticated
    @inlineCallbacks
    def post(self):
        request = self.validate_message(self.request.body,
                                        requests.WizardDesc)

        # Wizard will raise exceptions if there are any errors with the request
        yield wizard(self.current_tenant, request, self.request.language)
        # cache must be updated in order to set wizard_done = True
        yield serialize_node(self.current_tenant, self.request.language)
        GLApiCache.invalidate(self.current_tenant)

        self.set_status(201)  # Created
