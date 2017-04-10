# -*- coding: UTF-8
# custodian
# ********
#
# Implement the classes handling the requests performed to /custodian/* URI PATH

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.utils.structures import Rosetta
from globaleaks.utils.utility import datetime_to_ISO8601, datetime_now


def serialize_identityaccessrequest(identityaccessrequest, language):
    iar = {
        'id': identityaccessrequest.id,
        'receivertip_id': identityaccessrequest.receivertip_id,
        'request_date': datetime_to_ISO8601(identityaccessrequest.request_date),
        'request_user_name': identityaccessrequest.receivertip.receiver.user.name,
        'request_motivation': identityaccessrequest.request_motivation,
        'reply_date': datetime_to_ISO8601(identityaccessrequest.reply_date),
        'reply_user_name': identityaccessrequest.reply_user.name \
                if identityaccessrequest.reply_user is not None else '',
        'reply': identityaccessrequest.reply,
        'reply_motivation': identityaccessrequest.reply_motivation,
        'submission_date': datetime_to_ISO8601(identityaccessrequest.receivertip.internaltip.creation_date)
    }

    mo = Rosetta(identityaccessrequest.receivertip.internaltip.context.localized_keys)
    mo.acquire_storm_object(identityaccessrequest.receivertip.internaltip.context)
    iar["submission_context"] = mo.dump_localized_key('name', language)

    return iar


@transact
def get_identityaccessrequest_list(store, tid, language):
    iars = store.find(models.IdentityAccessRequest, tid=tid, reply=u'pending')

    return [serialize_identityaccessrequest(iar, language) for iar in iars]


def db_get_identityaccessrequest(store, tid, identityaccessrequest_id):
    return models.IdentityAccessRequest.db_get(store, tid=tid, id=identityaccessrequest_id)


@transact
def get_identityaccessrequest(store, tid, identityaccessrequest_id, language):
    iar = db_get_identityaccessrequest(store, tid, identityaccessrequest_id)
    return serialize_identityaccessrequest(iar, language)


@transact
def update_identityaccessrequest(store, tid, user_id, identityaccessrequest_id, request, language):
    iar = db_get_identityaccessrequest(store, tid, identityaccessrequest_id)

    if iar.reply == 'pending':
        iar.reply_date = datetime_now()
        iar.reply_user_id = user_id
        iar.reply = request['reply']
        if iar.reply == 'authorized':
            iar.receivertip.can_access_whistleblower_identity = True
        iar.reply_motivation = request['reply_motivation']

    return serialize_identityaccessrequest(iar, language)


class IdentityAccessRequestInstance(BaseHandler):
    """
    This handler allow custodians to manage an identity access request by a receiver
    """
    @BaseHandler.transport_security_check('custodian')
    @BaseHandler.authenticated('custodian')
    @inlineCallbacks
    def get(self, identityaccessrequest_id):
        """
        Parameters: the id of the identity access request
        Response: IdentityAccessRequestDesc
        Errors: IdentityAccessRequestIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        identityaccessrequest = yield get_identityaccessrequest(self.current_tenant,
                                                                identityaccessrequest_id,
                                                                self.request.language)

        self.write(identityaccessrequest)


    @BaseHandler.transport_security_check('custodian')
    @BaseHandler.authenticated('custodian')
    @inlineCallbacks
    def put(self, identityaccessrequest_id):
        """
        Parameters: the id of the identity access request
        Request: IdentityAccessRequestDesc
        Response: IdentityAccessRequestDesc
        Errors: IdentityAccessRequestIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        request = self.validate_message(self.request.body, requests.CustodianIdentityAccessRequestDesc)

        identityaccessrequest = yield update_identityaccessrequest(self.current_tenant,
                                                                   self.current_user.user_id,
                                                                   identityaccessrequest_id,
                                                                   request,
                                                                   self.request.language)

        self.write(identityaccessrequest)


class IdentityAccessRequestsCollection(BaseHandler):
    """
    This interface return the list of the requests of access to whislteblower identities
    GET /identityrequests
    """

    @BaseHandler.transport_security_check('custodian')
    @BaseHandler.authenticated('custodian')
    @inlineCallbacks
    def get(self):
        """
        Response: identityaccessrequestsList
        Errors: InvalidAuthentication
        """
        answer = yield get_identityaccessrequest_list(self.current_tenant,
                                                      self.request.language)

        self.write(answer)
