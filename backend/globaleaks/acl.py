from globaleaks import models
from globaleaks.rest import errors


def user_match(list1, list2):
    return len(list(set(list1) & set(list2))) != 0


def db_access_tenant(store, rstate, tenant_id):
    if rstate.user.user_id not in rstate.app_state.user_tenant_map or \
       not user_match([tenant_id], rstate.app_state.user_tenant_map[rstate.user.user_id]):
        raise errors.InvalidAuthentication()


def db_access_context(store, rstate, context_id):
    context = models.Context.db_get(store, id=unicode(context_id), tid=rstate.tid)

    if rstate.user.user_id not in rstate.app_state.user_tenant_map or \
       not user_match([context.tid], rstate.app_state.user_tenant_map[rstate.user.user_id]):
        raise errors.InvalidAuthentication()

    return context


def db_access_user(store, rstate, user_id):
    user = models.User.db_get(store, id=unicode(user_id))

    if rstate.user.user_id not in rstate.app_state.user_tenant_map or \
       user.id not in rstate.app_state.user_tenant_map or \
       not user_match(rstate.app_state.user_tenant_map[user_id],
                      rstate.app_state.user_tenant_map[rstate.user.user_id]):
        raise errors.InvalidAuthentication()
    
    return user
    
    
def db_access_receiver(store, rstate, receiver_id):
    receiver = models.Receiver.db_get(store, id=unicode(context_id), tid=rstate.tid)

    if rstate.user.user_id not in rstate.app_state.user_tenant_map or \
       receiver.id not in rstate.app_state.user_tenant_map or \
       not user_match(rstate.app_state.user_tenant_map[receiver_id],
                   rstate.app_state.user_tenant_map[rstate.user.user_id]):
        raise errors.InvalidAuthentication()

    return receiver


def db_get_question_tenant(field):
    return field.id


def db_get_step_tenant(step):
    return [t.id for t in step.questionnaire.tenants]


def db_get_field_tenant(field):
    if field.fieldgroup_id:
        print 1
        return db_get_field_tenant(field.fieldgrup)

    if field.step_id:
        print 2
        return db_get_step_tenant(field.step)

    if field.question_id:
        print 3
        return field.question.db_get_question_tenant(field.question)


def db_access_field(store, rstate, field_id):
    field = models.Field.db_get(store, id=unicode(field_id))

    tids = db_get_field_tenant(field)

    if rstate.user.user_id not in rstate.app_state.user_tenant_map or \
       not user_match(tids,
                      rstate.app_state.user_tenant_map[rstate.user.user_id]):
        raise errors.InvalidAuthentication()

    return field
