# -*- coding: UTF-8
#
#   user
#   *****
# Implementation of the User model functionalities
#
from twisted.internet.defer import inlineCallbacks

from globaleaks import models, security
from globaleaks.acl import db_access_user, db_access_tenant
from globaleaks.handlers.admin.context import db_associate_receiver_contexts
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.user import apply_pgp_options, user_serialize_user
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.rest.apicache import GLApiCache
from globaleaks.utils.structures import fill_localized_keys
from globaleaks.utils.utility import log, datetime_now
from globaleaks.state import app_state


def db_create_user(store, tid, request, language):
    fill_localized_keys(request, models.User.localized_keys, language)

    apply_pgp_options(request)

    user = models.User({
        'role': request['role'],
        'state': u'enabled',
        'deletable': request['deletable'],
        'name': request['name'],
        'description': request['description'],
        'public_name': request['public_name'] if request['public_name'] != '' else request['name'],
        'language': language,
        'password_change_needed': request['password_change_needed'],
        'mail_address': request['mail_address'],
        'pgp_key_fingerprint': request['pgp_key_fingerprint'],
        'pgp_key_public': request['pgp_key_public'],
        'pgp_key_expiration': request['pgp_key_expiration']
    })

    password = request['password']
    if len(password) == 0:
        password = app_state.tenant_states[tid].memc.default_password

    user.salt = security.generateRandomSalt()
    user.password = security.hash_password(password, user.salt)

    store.add(user)

    tenant = store.get(models.Tenant, tid)

    tenant.users.add(user)

    return user


def db_create_receiver(store, tid, request, language):
    """
    Creates a new receiver
    Returns:
        (dict) the receiver descriptor
    """
    user = db_create_user(store, tid, request, language)

    fill_localized_keys(request, models.Receiver.localized_keys, language)

    receiver = models.Receiver(request)

    # set receiver.id user.id
    receiver.id = user.id

    store.add(receiver)

    db_associate_receiver_contexts(store, receiver, request['contexts'])

    log.debug("Created new receiver")

    return receiver


@transact
def create_receiver_user(store, tid, request, language):
    receiver = db_create_receiver(store, tid, request, language)
    return user_serialize_user(store, receiver.user, language)



def db_update_user(store, user, request, language):
    """
    Updates the specified user.
    raises: globaleaks.errors.UserIdNotFound` if the user does not exist.
    """
    fill_localized_keys(request, models.User.localized_keys, language)

    apply_pgp_options(request)

    user.update(request)

    password = request['password']
    if len(password) > 0:
        user.password = security.hash_password(password, user.salt)
        user.password_change_date = datetime_now()

    return user


@transact
def update_user(store, rstate, user_id, request, language):
    user = db_access_user(store, rstate, user_id)

    user = db_update_user(store, user, request, language)

    return user_serialize_user(store, user, language)


@transact
def get_user(store, rstate, user_id, language):
    user = db_access_user(store, rstate, user_id)

    return user_serialize_user(store, user, language)


def db_system_get_admin_users(store, tid):
    users = store.find(models.User, models.User.role == u'admin',
                                    models.User.id == models.User_Tenant.user_id,
                                    models.User_Tenant.tenant_id == tid)

    return [user_serialize_user(store, user, app_state.tenant_states[tid].memc.default_language) for user in users]


@transact
def delete_user(store, rstate, user_id):
    user = db_access_user(store, rstate, user_id)

    if not user.deletable:
        raise errors.UserNotDeletable

    store.remove(user)


def db_get_user_list(store, tid):
    return store.find(models.User, models.User.id == models.User_Tenant.user_id,
                                   models.User_Tenant.tenant_id == tid)


@transact
def get_user_list(store, rstate, language):
    """
    Returns:
        (list) the list of users
    """
    db_access_tenant(store, rstate, rstate.tid)

    users = db_get_user_list(store, rstate.tid)

    return [user_serialize_user(store, user, language) for user in users]


class UsersCollection(BaseHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Return all the users.

        Parameters: None
        Response: adminUsersList
        Errors: None
        """
        response = yield get_user_list(self.req_state,
                                       self.request.language)

        self.write(response)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Create a new user

        Request: AdminUserDesc
        Response: AdminUserDesc
        Errors: InvalidInputFormat, UserIdNotFound
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminUserDesc)

        if request['role'] == 'receiver':
            if 'contexts' not in request:
                request['contexts'] = []

            response = yield create_receiver_user(self.current_tenant, request, self.request.language)
        elif request['role'] == 'custodian':
            response = yield create_user(self.current_tenant, request, self.request.language)
        elif request['role'] == 'admin':
            response = yield create_user(self.current_tenant, request, self.request.language)
        else:
            raise errors.InvalidInputFormat

        yield app_state.refresh()

        GLApiCache.invalidate(self.current_tenant)

        self.write(response)


class UserInstance(BaseHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def get(self, user_id):
        """
        Get the specified user.

        Parameters: user_id
        Response: AdminUserDesc
        Errors: InvalidInputFormat, UserIdNotFound
        """
        response = yield get_user(self.req_state,
                                  user_id,
                                  self.request.language)

        self.write(response)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def put(self, user_id):
        """
        Update the specified user.

        Parameters: user_id
        Request: AdminUserDesc
        Response: AdminUserDesc
        Errors: InvalidInputFormat, UserIdNotFound
        """
        request = self.validate_message(self.request.body, requests.AdminUserDesc)

        response = yield update_user(self.req_state,
                                     user_id,
                                     request,
                                     self.request.language)

        GLApiCache.invalidate(self.current_tenant)

        self.write(response)

    @inlineCallbacks
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def delete(self, user_id):
        """
        Delete the specified user.

        Parameters: user_id
        Request: None
        Response: None
        Errors: InvalidInputFormat, UserIdNotFound
        """
        yield delete_user(self.req_state, user_id)

        GLApiCache.invalidate(self.current_tenant)
