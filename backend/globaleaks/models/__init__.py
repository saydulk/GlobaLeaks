# -*- coding: UTF-8
from storm.locals import Bool, Int, Reference, ReferenceSet, Unicode, Storm, JSON

from globaleaks.models.config import Config
from globaleaks.models.l10n import ConfigL10N, EnabledLanguage
from globaleaks.models.models import Model, ModelWithID, ModelWithTID, ModelWithIDandTID
from globaleaks.models.properties import DateTime
from globaleaks.models.validators import shorttext_v, longtext_v, \
    shortlocal_v, longlocal_v, shorturl_v, longurl_v, natnum_v, range_v

from globaleaks.orm import transact

from globaleaks.utils.utility import datetime_now, datetime_null, uuid4

empty_localization = {}

class Tenant(Model):
    """
    Class used to implement tenants
    """
    id = Int(primary=True)
    label = Unicode(validator=shorttext_v)
    https_hostname = Unicode(validator=shorttext_v)
    onion_hostname = Unicode(validator=shorttext_v)

    unicode_keys = ['label', 'https_hostname']


class User(ModelWithID):
    """
    This model keeps track of globaleaks users.
    """
    creation_date = DateTime(default_factory=datetime_now)

    username = Unicode(validator=shorttext_v)

    password = Unicode()
    salt = Unicode()

    deletable = Bool(default=True)

    name = Unicode(validator=shorttext_v, default=u'')
    description = JSON(validator=longlocal_v, default={})

    public_name = Unicode(validator=shorttext_v, default=u'')

    # roles: 'admin', 'receiver', 'custodian'
    role = Unicode()
    state = Unicode(default=u'enabled')
    last_login = DateTime(default_factory=datetime_null)
    mail_address = Unicode(default=u'')
    language = Unicode()
    password_change_needed = Bool(default=True)
    password_change_date = DateTime(default_factory=datetime_null)

    # BEGIN of PGP key fields
    pgp_key_fingerprint = Unicode(default=u'')
    pgp_key_public = Unicode(default=u'')
    pgp_key_expiration = DateTime(default_factory=datetime_null)
    # END of PGP key fields

    unicode_keys = ['username', 'role', 'state',
                    'language', 'mail_address', 'name',
                    'public_name', 'pgp_key_fingerprint',
                    'pgp_key_public']

    localized_keys = ['description']

    bool_keys = ['deletable', 'password_change_needed']

    datetime_keys = ['pgp_key_expiration']


class UserImg(ModelWithID):
    data = Unicode()

    unicode_keys=['id', 'data']


class Context(ModelWithIDandTID):
    """
    This model keeps track of contexts settings.
    """
    show_small_receiver_cards = Bool(default=False)
    show_context = Bool(default=True)
    show_recipients_details = Bool(default=False)
    allow_recipients_selection = Bool(default=False)
    maximum_selectable_receivers = Int(default=0)
    select_all_receivers = Bool(default=True)

    enable_comments = Bool(default=True)
    enable_messages = Bool(default=False)
    enable_two_way_comments = Bool(default=True)
    enable_two_way_messages = Bool(default=True)
    enable_attachments = Bool(default=True) # Lets WB attach files to submission
    enable_rc_to_wb_files = Bool(default=False) # The name says it all folks

    tip_timetolive = Int(validator=range_v(-1, 5*365), default=15) # in days, -1 indicates no expiration

    # localized strings
    name = JSON(validator=shortlocal_v, default={})
    description = JSON(validator=longlocal_v, default={})
    recipients_clarification = JSON(validator=longlocal_v, default={})

    status_page_message = JSON(validator=longlocal_v, default={})

    show_receivers_in_alphabetical_order = Bool(default=False)

    presentation_order = Int(default=0)

    questionnaire_id = Unicode()

    unicode_keys = ['questionnaire_id']

    localized_keys = ['name', 'description', 'recipients_clarification', 'status_page_message']

    int_keys = [
      'tip_timetolive',
      'maximum_selectable_receivers',
      'presentation_order',
      'steps_navigation_requires_completion'
    ]

    bool_keys = [
      'select_all_receivers',
      'show_small_receiver_cards',
      'show_context',
      'show_recipients_details',
      'show_receivers_in_alphabetical_order',
      'allow_recipients_selection',
      'enable_comments',
      'enable_messages',
      'enable_two_way_comments',
      'enable_two_way_messages',
      'enable_attachments',
      'enable_rc_to_wb_files'
    ]


class ContextImg(ModelWithID):
    data = Unicode()

    unicode_keys=['id', 'data']


class InternalTip(ModelWithID):
    """
    This is the internal representation of a Tip that has been submitted to the
    GlobaLeaks node.

    It has a not associated map for keep track of Receivers, Tips,
    Comments and WhistleblowerTip.
    All of those element has a Storm Reference with the InternalTip.id,
    never vice-versa
    """
    creation_date = DateTime(default_factory=datetime_now)
    update_date = DateTime(default_factory=datetime_now)

    context_id = Unicode()

    questionnaire_hash = Unicode()
    preview = JSON()
    progressive = Int(default=0)
    tor2web = Bool(default=False)
    total_score = Int(default=0)
    expiration_date = DateTime()

    identity_provided = Bool(default=False)
    identity_provided_date = DateTime(default_factory=datetime_null)

    enable_two_way_comments = Bool(default=True)
    enable_two_way_messages = Bool(default=True)
    enable_attachments = Bool(default=True)
    enable_whistleblower_identity = Bool(default=False)

    wb_last_access = DateTime(default_factory=datetime_now)
    wb_access_counter = Int(default=0)

    # def wb_revoke_access_date(self):
    # NOTE removed in (tid_state) changes

    def is_wb_access_revoked(self):
        return self.whistleblowertip is None


class ReceiverTip(ModelWithID):
    """
    This is the table keeping track of ALL the receivers activities and
    date in a Tip, Tip core data are stored in StoredTip. The data here
    provide accountability of Receiver accesses, operations, options.
    """
    internaltip_id = Unicode()
    receiver_id = Unicode()

    last_access = DateTime(default_factory=datetime_null)
    access_counter = Int(default=0)

    label = Unicode(default=u'')

    can_access_whistleblower_identity = Bool(default=False)

    new = Int(default=True)

    enable_notifications = Bool(default=True)

    unicode_keys = ['label']

    bool_keys = ['enable_notifications']


class WhistleblowerTip(ModelWithID):
    """
    WhisteleblowerTip implement the expiring authentication token for
    the whistleblower and acts as interface to the InternalTip.
    """
    receipt_hash = Unicode()


class IdentityAccessRequest(ModelWithIDandTID):
    """
    This model keeps track of identity access requests by receivers and
    of the answers by custodians.
    """
    receivertip_id = Unicode()
    request_date = DateTime(default_factory=datetime_now)
    request_motivation = Unicode(default=u'')
    reply_date = DateTime(default_factory=datetime_null)
    reply_user_id = Unicode()
    reply_motivation = Unicode(default=u'')
    reply = Unicode(default=u'pending')


class InternalFile(ModelWithID):
    """
    This model keeps track of files before they are packaged
    for specific receivers.
    """
    creation_date = DateTime(default_factory=datetime_now)

    internaltip_id = Unicode()

    name = Unicode(validator=longtext_v)
    file_path = Unicode()

    content_type = Unicode()
    size = Int()

    new = Int(default=True)

    submission = Int(default = False)

    processing_attempts = Int(default=0)


class ReceiverFile(ModelWithID):
    """
    This model keeps track of files destinated to a specific receiver
    """
    internalfile_id = Unicode()
    receivertip_id = Unicode()
    file_path = Unicode()
    size = Int()
    downloads = Int(default=0)
    last_access = DateTime(default_factory=datetime_null)

    new = Int(default=True)

    status = Unicode()
    # statuses: 'reference', 'encrypted', 'unavailable', 'nokey'
    # reference = receiverfile.file_path reference internalfile.file_path
    # encrypted = receiverfile.file_path is an encrypted file for
    #                                    the specific receiver
    # unavailable = the file was supposed to be available but something goes
    # wrong and now is lost


class WhistleblowerFile(ModelWithID):
    """
    This models stores metadata of files uploaded by recipients intended to be
    delivered to the whistleblower. This file is not encrypted and nor is it
    integrity checked in any meaningful way.
    """
    receivertip_id = Unicode()

    name = Unicode(validator=shorttext_v)
    file_path = Unicode()
    size = Int()
    content_type = Unicode()
    downloads = Int(default=0)
    creation_date = DateTime(default_factory=datetime_now)
    last_access = DateTime(default_factory=datetime_null)
    description = Unicode(validator=longtext_v)


class Comment(ModelWithID):
    """
    This table handle the comment collection, has an InternalTip referenced
    """
    creation_date = DateTime(default_factory=datetime_now)

    internaltip_id = Unicode()

    author_id = Unicode()
    content = Unicode(validator=longtext_v)

    type = Unicode()
    # types: 'receiver', 'whistleblower'

    new = Int(default=True)


class Message(ModelWithID):
    """
    This table handle the direct messages between whistleblower and one
    Receiver.
    """
    creation_date = DateTime(default_factory=datetime_now)

    receivertip_id = Unicode()
    content = Unicode(validator=longtext_v)

    type = Unicode()
    # types: 'receiver', whistleblower'

    new = Int(default=True)


class Mail(ModelWithID):
    """
    This model keeps track of emails to be spooled by the system
    """
    creation_date = DateTime(default_factory=datetime_now)

    address = Unicode()
    subject = Unicode()
    body = Unicode()

    processing_attempts = Int(default=0)

    unicode_keys = ['address', 'subject', 'body']


class Receiver(ModelWithID):
    """
    This model keeps track of receivers settings.
    """
    configuration = Unicode(default=u'default')
    # configurations: 'default', 'forcefully_selected', 'unselectable'

    # Admin chosen options
    can_delete_submission = Bool(default=False)
    can_postpone_expiration = Bool(default=False)
    can_grant_permissions = Bool(default=False)

    tip_notification = Bool(default=True)

    presentation_order = Int(default=0)

    unicode_keys = ['configuration']

    int_keys = ['presentation_order']

    bool_keys = [
        'can_delete_submission',
        'can_postpone_expiration',
        'can_grant_permissions',
        'tip_notification',
    ]


class Field(ModelWithID):
    x = Int(default=0)
    y = Int(default=0)
    width = Int(default=0)

    key = Unicode(default=u'')

    label = JSON(validator=longlocal_v)
    description = JSON(validator=longlocal_v)
    hint = JSON(validator=longlocal_v)

    required = Bool(default=False)
    preview = Bool(default=False)

    multi_entry = Bool(default=False)
    multi_entry_hint = JSON(validator=shortlocal_v)

    # This is set if the field should be duplicated for collecting statistics
    # when encryption is enabled.
    stats_enabled = Bool(default=False)

    triggered_by_score = Int(default=0)

    question_id = Unicode()
    step_id = Unicode()
    fieldgroup_id = Unicode()
    template_id = Unicode()

    type = Unicode(default=u'inputbox')

    editable = Bool(default=True)

    unicode_keys = ['type', 'key', 'question_id', 'step_id', 'fieldgroup_id', 'template_id']
    int_keys = ['x', 'y', 'width', 'triggered_by_score']
    localized_keys = ['label', 'description', 'hint', 'multi_entry_hint']
    bool_keys = ['editable', 'multi_entry', 'preview', 'required', 'stats_enabled']

    @classmethod
    def db_delete(cls, store, *args, **kwargs):
        obj = store.find(cls, *args, **kwargs).one()
        if obj.question:
            store.remove(obj.question)
        else:
            store.remove(obj)


class FieldAttr(ModelWithID):
    field_id = Unicode()
    name = Unicode()
    type = Unicode()
    value = JSON()

    unicode_keys = ['field_id', 'name', 'type', 'triggered_step', 'trigger_field']

    def update(self, values=None):
        Model.update(self, values)

        if values is None:
            return

        if self.type == 'localized':
            value = values['value']
            previous = getattr(self, 'value')

            if previous and isinstance(previous, dict):
                previous.update(value)
                setattr(self, 'value', previous)
            else:
                setattr(self, 'value', value)
        else:
            setattr(self, 'value', unicode(values['value']))


class FieldOption(ModelWithID):
    field_id = Unicode()
    presentation_order = Int(default=0)
    label = JSON()
    score_points = Int(default=0)
    trigger_field = Unicode()
    trigger_step = Unicode()

    unicode_keys = ['field_id']
    int_keys = ['presentation_order', 'score_points']
    localized_keys = ['label']


class FieldAnswer(ModelWithID):
    internaltip_id = Unicode()
    fieldanswergroup_id = Unicode()
    key = Unicode(default=u'')
    is_leaf = Bool(default=True)
    value = Unicode(default=u'')

    unicode_keys = ['internaltip_id', 'key', 'value']
    bool_keys = ['is_leaf']


class FieldAnswerGroup(ModelWithID):
    number = Int(default=0)
    fieldanswer_id = Unicode()

    unicode_keys = ['fieldanswer_id']
    int_keys = ['number']


class Step(ModelWithID):
    questionnaire_id = Unicode()
    label = JSON()
    description = JSON()
    presentation_order = Int(default=0)
    triggered_by_score = Int(default=0)

    unicode_keys = ['questionnaire_id']
    int_keys = ['presentation_order', 'triggered_by_score']
    localized_keys = ['label', 'description']


class Questionnaire(ModelWithID):
    key = Unicode(default=u'')
    name = Unicode()
    show_steps_navigation_bar = Bool(default=False)
    steps_navigation_requires_completion = Bool(default=False)
    enable_whistleblower_identity = Bool(default=False)

    editable = Bool(default=True)

    unicode_keys = ['name', 'key']

    bool_keys = [
      'editable',
      'show_steps_navigation_bar',
      'steps_navigation_requires_completion'
    ]


class Question(ModelWithID):
    pass


class ArchivedSchema(Model):
    __storm_primary__ = 'hash', 'type'

    hash = Unicode()
    type = Unicode()
    schema = JSON()

    unicode_keys = ['hash']


class Stats(ModelWithID):
    start = DateTime()
    summary = JSON()
    free_disk_space = Int()


class Anomalies(ModelWithID):
    date = DateTime()
    alarm = Int()
    events = JSON()


class SecureFileDelete(ModelWithID):
    filepath = Unicode()


class Counter(ModelWithTID):
    """
    Class used to implement unique counters
    """
    __storm_primary__  = 'tid', 'key'

    key = Unicode(validator=shorttext_v)
    counter = Int(default=1)
    update_date = DateTime(default_factory=datetime_now)

    unicode_keys = ['key']
    int_keys = ['tid', 'number']


class ShortURL(ModelWithIDandTID):
    """
    Class used to implement url shorteners
    """
    shorturl = Unicode(validator=shorturl_v)
    longurl = Unicode(validator=longurl_v)

    unicode_keys = ['shorturl', 'longurl']


class CustomTexts(ModelWithTID):
    """
    Class used to implement custom texts
    """
    __storm_primary__ = 'tid', 'lang'

    lang = Unicode(primary=True, validator=shorttext_v)
    texts = JSON()

    int_keys = ['tid']
    unicode_keys = ['lang']
    json_keys = ['texts']


# Follow classes used for Many to Many references
class User_Tenant(Model):
    """
    Class used to implement references between Users and Tenants
    """
    __storm_primary__ = 'user_id', 'tenant_id'

    user_id = Unicode()
    tenant_id = Int()


class Questionnaire_Tenant(Model):
    """
    Class used to implement references between Questionnaire and Tenants
    """
    __storm_primary__ = 'questionnaire_id', 'tenant_id'

    questionnaire_id = Unicode()
    tenant_id = Int()

    int_keys = ['tenant_id']
    unicode_keys = ['questionnaire_id']


class Question_Tenant(Model):
    """
    Class used to implement references between Questions and Tenants
    """
    __storm_primary__ = 'question_id', 'tenant_id'

    question_id = Unicode()
    tenant_id = Int()

    int_keys = ['tenant_id']
    unicode_keys = ['question_id']


class Receiver_Context(Model):
    """
    Class used to implement references between Receivers and Contexts
    """
    __storm_primary__ = 'context_id', 'receiver_id'

    context_id = Unicode()
    receiver_id = Unicode()


Context.img = Reference(Context.id, ContextImg.id)
User.img = Reference(User.id, UserImg.id)

Field.fieldgroup = Reference(Field.fieldgroup_id, Field.id)
Field.step = Reference(Field.step_id, Step.id)
Field.question = Reference(Field.question_id, Question.id)
Field.template = Reference(Field.template_id, Field.id)

Field.options = ReferenceSet(
    Field.id,
    FieldOption.field_id
)

Field.children = ReferenceSet(
    Field.id,
    Field.fieldgroup_id
)

Field.attrs = ReferenceSet(Field.id, FieldAttr.field_id)

Field.triggered_by_options = ReferenceSet(Field.id, FieldOption.trigger_field)
Step.triggered_by_options = ReferenceSet(Step.id, FieldOption.trigger_step)

FieldAnswer.groups = ReferenceSet(FieldAnswer.id, FieldAnswerGroup.fieldanswer_id)

FieldAnswerGroup.fieldanswers = ReferenceSet(
    FieldAnswerGroup.id,
    FieldAnswer.fieldanswergroup_id
)

Step.children = ReferenceSet(
    Step.id,
    Field.step_id
)

Context.questionnaire = Reference(Context.questionnaire_id, Questionnaire.id)

Questionnaire.steps = ReferenceSet(Questionnaire.id, Step.questionnaire_id)

Step.questionnaire = Reference(Step.questionnaire_id, Questionnaire.id)

Receiver.user = Reference(Receiver.id, User.id)

InternalTip.context = Reference(
    InternalTip.context_id,
    Context.id
)

InternalTip.answers = ReferenceSet(
    InternalTip.id,
    FieldAnswer.internaltip_id
)

InternalTip.comments = ReferenceSet(
    InternalTip.id,
    Comment.internaltip_id
)

InternalTip.whistleblowertip = Reference(
    InternalTip.id,
    WhistleblowerTip.id
)

InternalTip.receivertips = ReferenceSet(
    InternalTip.id,
    ReceiverTip.internaltip_id
)

ReceiverTip.messages = ReferenceSet(
    ReceiverTip.id,
    Message.receivertip_id
)

ReceiverTip.identityaccessrequests = ReferenceSet(
    ReceiverTip.id,
    IdentityAccessRequest.receivertip_id
)

InternalTip.internalfiles = ReferenceSet(
    InternalTip.id,
    InternalFile.internaltip_id
)

ReceiverFile.internalfile = Reference(
    ReceiverFile.internalfile_id,
    InternalFile.id
)

ReceiverFile.receivertip = Reference(
    ReceiverFile.receivertip_id,
    ReceiverTip.id
)

WhistleblowerFile.receivertip = Reference(
    WhistleblowerFile.receivertip_id,
    ReceiverTip.id
)

WhistleblowerTip.internaltip = Reference(
    WhistleblowerTip.id,
    InternalTip.id
)

InternalFile.internaltip = Reference(
    InternalFile.internaltip_id,
    InternalTip.id
)


ReceiverTip.internaltip = Reference(ReceiverTip.internaltip_id, InternalTip.id)

ReceiverTip.receiver = Reference(ReceiverTip.receiver_id, Receiver.id)

Comment.internaltip = Reference(Comment.internaltip_id, InternalTip.id)
Comment.author = Reference(Comment.author_id, User.id)

Message.receivertip = Reference(Message.receivertip_id, ReceiverTip.id)

IdentityAccessRequest.receivertip = Reference(
    IdentityAccessRequest.receivertip_id,
    ReceiverTip.id
)

IdentityAccessRequest.reply_user = Reference(
    IdentityAccessRequest.reply_user_id,
    User.id
)

Context.receivers = ReferenceSet(
    Context.id,
    Receiver_Context.context_id,
    Receiver_Context.receiver_id,
    Receiver.id
)

Receiver.contexts = ReferenceSet(
    Receiver.id,
    Receiver_Context.receiver_id,
    Receiver_Context.context_id,
    Context.id
)

User.tenants = ReferenceSet(
    User.id,
    User_Tenant.user_id,
    User_Tenant.tenant_id,
    Tenant.id
)

Tenant.users = ReferenceSet(
    Tenant.id,
    User_Tenant.tenant_id,
    User_Tenant.user_id,
    User.id
)

models_list = [
    Anomalies,
    ArchivedSchema,
    Comment,
    Config,
    ConfigL10N,
    Context,
    ContextImg,
    CustomTexts,
    EnabledLanguage,
    Field,
    FieldAnswer,
    FieldAnswerGroup,
    FieldAttr,
    FieldOption,
    IdentityAccessRequest,
    InternalFile,
    InternalTip,
    Mail,
    Message,
    Question,
    Question_Tenant,
    Receiver,
    Receiver_Context,
    ReceiverFile,
    ReceiverTip,
    Step,
    SecureFileDelete,
    ShortURL,
    Stats,
    Tenant,
    User,
    UserImg,
    User_Tenant,
    WhistleblowerFile,
    WhistleblowerTip
]
