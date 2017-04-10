# -*- coding: utf-8 -*-
#
# /admin/files
#  *****
#
# API handling db files upload/download/delete
import base64
from twisted.internet.defer import inlineCallbacks

from globaleaks.handlers.base import BaseHandler
from globaleaks.models.config import NodeFactory
from globaleaks.orm import transact
from globaleaks.rest.apicache import GLApiCache


def db_add_file(store, tid, key, data):
    data = base64.b64encode(data)
    NodeFactory(store, tid).set_val(key, data)


@transact
def add_file(store, tid, key, data):
    db_add_file(store, tid, key, data)


def db_del_file(store, tid, key):
    NodeFactory(store, tid).set_val(key, '')


@transact
def del_file(store, tid, key):
    db_del_file(store, tid, key)


class FileInstance(BaseHandler):
    key = None

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self, key):
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            self.set_status(201)
            return

        try:
            yield add_file(self.current_tenant,
                           key,
                           uploaded_file['body'].read())
        finally:
            uploaded_file['body'].close()

        GLApiCache.invalidate(self.current_tenant)

        self.set_status(201)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def delete(self, key):
        yield del_file(self.current_tenant, key)

        GLApiCache.invalidate(self.current_tenant)
