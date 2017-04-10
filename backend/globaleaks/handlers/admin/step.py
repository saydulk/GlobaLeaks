# -*- coding: UTF-8
#
#   /admin/steps
#   *****
# Implementation of the code executed on handler /admin/steps
#

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.admin.field import db_create_field, db_update_field
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.public import serialize_step
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.rest.apicache import GLApiCache
from globaleaks.utils.structures import fill_localized_keys


def db_get_step(store, tid, step_id):
    return store.find(models.Step, models.Step.id == step_id,
                                   models.Step.questionnaire_id == models.Questionnaire.id).one()


def db_create_step(store, tid, step_dict, language):
    """
    Create the specified step

    :param store: the store on which perform queries.
    :param language: the language of the specified steps.
    """
    fill_localized_keys(step_dict, models.Step.localized_keys, language)

    s = models.Step(step_dict)

    store.add(s)

    for c in step_dict['children']:
        c['step_id'] = s.id
        db_create_field(store, tid, c, language)

    return s


@transact
def create_step(store, tid, step, language):
    """
    Transaction that perform db_create_step
    """
    step = db_create_step(store, tid, step, language)
    return serialize_step(store, step, language)


def db_update_step(store, tid, step_id, request, language):
    """
    Update the specified step with the details.
    raises :class:`globaleaks.errors.StepIdNotFound` if the step does
    not exist.

    :param store: the store on which perform queries.
    :param step_id: the step_id of the step to update
    :param request: the step definition dict
    :param language: the language of the step definition dict
    :return: a serialization of the object
    """
    step = models.Step.db_get(store, id=step_id)

    fill_localized_keys(request, models.Step.localized_keys, language)

    step.update(request)

    for child in request['children']:
        db_update_field(store, child['id'], child, language)

    return step


@transact
def update_step(store, tid, step_id, request, language):
    return serialize_step(store, db_update_step(store, tid, step_id, request, language), language)


@transact
def get_step(store, tid, step_id, language):
    """
    Serialize the specified step

    :param store: the store on which perform queries.
    :param step_id: the id corresponding to the step.
    :param language: the language in which to localize data
    :return: the currently configured step.
    :rtype: dict
    """
    return serialize_step(store, db_get_step(store, tid, step_id), language)


@transact
def delete_step(store, tid, step_id):
    """
    Delete the step object corresponding to step_id

    If the step has children, remove them as well.

    :param store: the store on which perform queries.
    :param step_id: the id corresponding to the step.
    :raises StepIdNotFound: if no such step is found.
    """
    step = db_get_step(store, tid, step_id)
    if step:
        store.remove(step)


class StepCollection(BaseHandler):
    """
    Operation to create a step

    /admin/steps
    """
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Create a new step.

        :return: the serialized step
        :rtype: StepDesc
        :raises InvalidInputFormat: if validation fails.
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminStepDesc)

        response = yield create_step(self.current_tenant,
                                     request,
                                     self.request.language)

        GLApiCache.invalidate(self.current_tenant)

        self.set_status(201)
        self.write(response)


class StepInstance(BaseHandler):
    """
    Operation to iterate over a specific requested Step

    /admin/step
    """
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def get(self, step_id):
        """
        Get the step identified by step_id

        :param step_id:
        :return: the serialized step
        :rtype: StepDesc
        :raises StepIdNotFound: if there is no step with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        response = yield get_step(self.current_tenant,
                                  step_id, self.request.language)

        self.write(response)


    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def put(self, step_id):
        """
        Update attributes of the specified step

        :param step_id:
        :return: the serialized step
        :rtype: StepDesc
        :raises StepIdNotFound: if there is no step with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminStepDesc)

        response = yield update_step(self.current_tenant,
                                     step_id,
                                     request,
                                     self.request.language)

        GLApiCache.invalidate(self.current_tenant)

        self.set_status(202) # Updated
        self.write(response)


    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def delete(self, step_id):
        """
        Delete the specified step.

        :param step_id:
        :raises StepIdNotFound: if there is no step with such id.
        :raises InvalidInputFormat: if validation fails.
        """
        yield delete_step(self.current_tenant, step_id)

        GLApiCache.invalidate(self.current_tenant)
