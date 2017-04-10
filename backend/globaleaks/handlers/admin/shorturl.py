# -*- coding: UTF-8
#
#   shorturl
#   *****
# Implementation of the URL shortener handlers
#
from storm.expr import And
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import requests, errors


def serialize_shorturl(shorturl):
    return {
        'shorturl': shorturl.shorturl,
        'longurl': shorturl.longurl,
        'id': shorturl.id
    }


@transact
def get_shorturl_list(store, tid):
    shorturls = store.find(models.ShortURL,
                           models.ShortURL.tid == tid)
    return [serialize_shorturl(shorturl) for shorturl in shorturls]


@transact
def create_shorturl(store, tid, request):
    shorturl = models.ShortURL(request)
    shorturl.tid = tid
    store.add(shorturl)
    return serialize_shorturl(shorturl)


class ShortURLCollection(BaseHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Return the list of registered short urls
        """
        response = yield get_shorturl_list(self.current_tenant)

        self.write(response)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Create a new shorturl
        """
        request = self.validate_message(self.request.body, requests.AdminShortURLDesc)

        response = yield create_shorturl(self.current_tenant, request)

        self.set_status(201) # Created
        self.write(response)


class ShortURLInstance(BaseHandler):
    @inlineCallbacks
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def delete(self, shorturl_id):
        """
        Delete the specified shorturl.
        """
        yield models.ShortURL.delete(id=shorturl_id, tid=self.current_tenant)
