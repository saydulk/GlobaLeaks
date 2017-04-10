# -*- coding: UTF-8
#
#   user
#   *****
# Implementation of the User model functionalities
#
from twisted.internet.defer import inlineCallbacks

from globaleaks import models, security
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.user import apply_pgp_options, user_serialize_user
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.rest.apicache import GLApiCache
from globaleaks.utils.structures import fill_localized_keys
from globaleaks.utils.utility import log, datetime_now
from globaleaks.state import app_state


def db_create_admin_user(store, ten_state, request, language):
    """
    Creates a new admin
    Returns:
        (dict) the admin descriptor
    """
    user = db_create_user(store, ten_state, request, language)

    log.debug("Created new admin")

    # TODO (ten_state) this may change the global application state
    app_state.db_refresh_exception_delivery_list(store)

    return user


@transact
def create_admin_user(store, ten_state, request, language):
    new_admin = db_create_admin_user(store, ten_state, request, language)
    return user_serialize_user(store, new_admin, language)


def db_create_custodian_user(store, ten_state, request, language):
    """
    Creates a new custodian
    Returns:
        (dict) the custodian descriptor
    """
    user = db_create_user(store, ten_state, request, language)

    log.debug("Created new custodian")

    return user


@transact
def create_custodian_user(store, ten_state, request, language):
    new_custodian = db_create_custodian_user(store, ten_state, request, language)
    return user_serialize_user(store, new_custodian, language)


def db_create_receiver(store, ten_state, request, language):
    """
    Creates a new receiver
    Returns:
        (dict) the receiver descriptor
    """
    user = db_create_user(store, ten_state, request, language)

    fill_localized_keys(request, models.Receiver.localized_keys, language)

    receiver = models.Receiver(request)

    # set receiver.id user.id
    receiver.id = user.id

    store.add(receiver)

    log.debug("Created new receiver")

    return receiver


@transact
def create_receiver_user(store, ten_state, request, language):
    new_receiver = db_create_receiver(store, ten_state, request, language)
    return user_serialize_user(store, new_receiver.user, language)


def db_create_user(store, ten_state, request, language):
    fill_localized_keys(request, models.User.localized_keys, language)

    apply_pgp_options(request)

    user = models.User({
        'username': request['username'],
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

    if request['username'] == '':
        user.username = user.id

    password = request['password']
    if len(password) == 0:
        password = ten_state.memc.default_password

    user.salt = security.generateRandomSalt()
    user.password = security.hash_password(password, user.salt)

    store.add(user)

    tenant = store.get(models.Tenant, ten_state.id)

    tenant.users.add(user)

    return user


def db_admin_update_user(store, tid, user_id, request, language):
    """
    Updates the specified user.
    raises: globaleaks.errors.UserIdNotFound` if the user does not exist.
    """
    user = db_get_user(store, tid, user_id)

    fill_localized_keys(request, models.User.localized_keys, language)

    apply_pgp_options(request)

    user.update(request)

    password = request['password']
    if len(password) > 0:
        user.password = security.hash_password(password, user.salt)
        user.password_change_date = datetime_now()

    if user.role == 'admin':
        # TODO (ten_state) may not change delivery_list
        app_state.db_refresh_exception_delivery_list(store)

    return user


@transact
def admin_update_user(store, tid, user_id, request, language):
    user = db_admin_update_user(store, tid, user_id, request, language)
    return user_serialize_user(store, user, language)


def db_get_user(store, tid, user_id):
    return models.User.db_get(store,
                              models.User.id == user_id,
                              models.User.id == models.User_Tenant.user_id,
                              models.User_Tenant.tenant_id == tid)


@transact
def get_user(store, tid, user_id, language):
    return user_serialize_user(store, db_get_user(store, tid, user_id), language)


def db_get_admin_users(store, ten_state):
    users = store.find(models.User, models.User.role == u'admin',
                                    models.User.id == models.User_Tenant.user_id,
                                    models.User_Tenant.tenant_id == ten_state.id)

    return [user_serialize_user(store, user, ten_state.memc.default_language) for user in users]


@transact
def delete_user(store, tid, user_id):
    user = db_get_user(store, tid, user_id)

    if not user.deletable:
        raise errors.UserNotDeletable

    store.remove(user)


def db_get_user_list(store, tid):
    return store.find(models.User, models.User.id == models.User_Tenant.user_id,
                                   models.User_Tenant.tenant_id == tid)


@transact
def get_user_list(store, tid, language):
    """
    Returns:
        (list) the list of users
    """
    return [user_serialize_user(store, user, language) for user in db_get_user_list(store, tid)]


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
        response = yield get_user_list(self.current_tenant,
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

        ts = self.ten_state

        if request['role'] == 'receiver':
            response = yield create_receiver_user(ts, request, self.request.language)
        elif request['role'] == 'custodian':
            response = yield create_custodian_user(ts, request, self.request.language)
        elif request['role'] == 'admin':
            response = yield create_admin_user(ts, request, self.request.language)
        else:
            raise errors.InvalidInputFormat

        GLApiCache.invalidate(self.current_tenant)

        self.set_status(201) # Created
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
        response = yield get_user(self.current_tenant,
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

        response = yield admin_update_user(self.current_tenant,
                                           user_id,
                                           request,
                                           self.request.language)

        GLApiCache.invalidate(self.current_tenant)

        self.set_status(201)
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
        yield delete_user(self.current_tenant, user_id)

        GLApiCache.invalidate(self.current_tenant)
