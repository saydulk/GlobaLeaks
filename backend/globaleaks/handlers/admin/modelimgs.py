# -*- coding: utf-8 -*-
#
# modelimgs
#  *****
#
# API handling upload/delete of users/contexts picture

import base64

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest.apicache import GLApiCache

model_map = {
  'users': models.UserImg,
  'contexts': models.ContextImg
}

def db_get_model_img(store, model_name, obj_id):
    model = model_map[model_name]
    obj = store.find(model, id=obj_id).one()
    return obj.data if obj else ''


@transact
def get_model_img(store, model_name, obj_id):
    return db_get_model_img(store, model_name, obj_id)


@transact
def add_model_img(store, tid, model_name, obj_id, data):
    model = model_map[model_name]
    data = base64.b64encode(data)

    db_del_model_img(store, model_name, obj_id)
    store.add(model({'id': obj_id, 'data': data}))


def db_del_model_img(store, model_name, obj_id):
    model = model_map[model_name]
    store.find(model, id=obj_id).remove()


@transact
def del_model_img(store, model_name, obj_id):
    db_del_model_img(store, model_name, obj_id)


class ModelImgInstance(BaseHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self, model_name, obj_id):
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            self.set_status(201)
            return

        try:
            yield add_model_img(self.current_tenant, model_name, obj_id, uploaded_file['body'].read())
        finally:
            uploaded_file['body'].close()

        GLApiCache.invalidate(self.current_tenant)

        self.set_status(201)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def delete(self, model_name, obj_id):
        yield del_model_img(model_name, obj_id)

        GLApiCache.invalidate(self.current_tenant)
