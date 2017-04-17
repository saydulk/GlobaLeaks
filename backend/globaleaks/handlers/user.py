# -*- coding: UTF-8
# user
# ********
#
# Implement the classes handling the requests performed to /user/* URI PATH

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.admin.modelimgs import db_get_model_img
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.security import change_password, parse_pgp_key
from globaleaks.settings import GLSettings
from globaleaks.utils.structures import get_localized_values
from globaleaks.utils.utility import datetime_to_ISO8601, datetime_now, datetime_null


def apply_pgp_options(request):
    """
    Parses pgp info included in the request and overwrites fields of the
    request.

    @param request: the dictionary containing the pgp infos to be parsed
    @return: None
    """
    if not request['pgp_key_remove'] and request['pgp_key_public'] != '':
        k = parse_pgp_key(request['pgp_key_public'])
        if k is not None:
            request['pgp_key_public'] = k['public']
            request['pgp_key_fingerprint'] = k['fingerprint']
            request['pgp_key_expiration'] = k['expiration']
            return

    request['pgp_key_public'] = ''
    request['pgp_key_fingerprint'] = ''
    request['pgp_key_expiration'] = datetime_null()


def user_serialize_user(store, user, language):
    """
    Serialize user description

    :param store: the store on which perform queries.
    :param username: the username of the user to be serialized
    :return: a serialization of the object
    """
    ret_dict = {
        'id': user.id,
        'password': '',
        'old_password': u'',
        'salt': '',
        'role': user.role,
        'deletable': user.deletable,
        'state': user.state,
        'last_login': datetime_to_ISO8601(user.last_login),
        'name': user.name,
        'public_name': user.public_name,
        'description': user.description,
        'mail_address': user.mail_address,
        'language': user.language,
        'password_change_needed': user.password_change_needed,
        'password_change_date': datetime_to_ISO8601(user.password_change_date),
        'pgp_key_fingerprint': user.pgp_key_fingerprint,
        'pgp_key_public': user.pgp_key_public,
        'pgp_key_expiration': datetime_to_ISO8601(user.pgp_key_expiration),
        'pgp_key_remove': False,
        'picture': user.img.data if user.img else ''
    }

    return get_localized_values(ret_dict, user, user.localized_keys, language)


@transact
def get_user_settings(store, user_id, language):
    user = models.User.db_get(store, id=user_id)
    return user_serialize_user(store, user, language)


def db_user_update_user(store, user_id, request, language):
    """
    Updates the specified user.
    This version of the function is specific for users that with comparison with
    admins can change only few things:
      - preferred language
      - the password (with old password check)
      - pgp key
    raises: globaleaks.errors.ReceiverIdNotFound` if the receiver does not exist.
    """
    user = models.User.db_get(store, id=user_id)

    apply_pgp_options(request)

    user.pgp_key_public = request['pgp_key_public']
    user.pgp_key_fingerprint = request['pgp_key_fingerprint']
    user.pgp_key_expiration = request['pgp_key_expiration']

    new_password = request['password']
    old_password = request['old_password']

    if len(new_password) and len(old_password):
        user.password = change_password(user.password,
                                        old_password,
                                        new_password,
                                        user.salt)

        if user.password_change_needed:
            user.password_change_needed = False

        user.password_change_date = datetime_now()

    return user


@transact
def update_user_settings(store, user_id, request, language):
    user = db_user_update_user(store, user_id, request, language)
    return user_serialize_user(store, user, language)


class UserInstance(BaseHandler):
    """
    This handler allow users to modify some of their fields:
        - language
        - password
        - notification settings
        - pgp key
    """
    @BaseHandler.authenticated('*')
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: ReceiverReceiverDesc
        Errors: UserIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        user_status = yield get_user_settings(self.current_user.user_id,
                                              self.request.language)

        self.write(user_status)


    @BaseHandler.authenticated('*')
    @inlineCallbacks
    def put(self):
        """
        Parameters: None
        Request: UserUserDesc
        Response: UserUserDesc
        Errors: UserIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        request = self.validate_message(self.request.body, requests.UserUserDesc)

        user_status = yield update_user_settings(self.current_user.user_id,
                                                 request,
                                                 self.request.language)

        self.write(user_status)
