# -*- coding: UTF-8

from storm.expr import And
from storm.locals import Bool, Int, Reference, ReferenceSet, Unicode, Storm, JSON

from globaleaks.constants import ROOT_TENANT
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.handlers.admin import tenant
from globaleaks.models.validators import shorttext_v, longtext_v, \
    shortlocal_v, longlocal_v, shorturl_v, longurl_v, natnum_v, range_v
from globaleaks.models import *
from globaleaks.utils.utility import datetime_now

from globaleaks.db.migrations.update_37.config_desc import GLConfig


class Config_v_36(Storm):
    __storm_table__ = 'config'
    __storm_primary__ = ('var_group', 'var_name')

    cfg_desc = GLConfig
    var_group = Unicode()
    var_name = Unicode()
    value = JSON()
    customized = Bool(default=False)

    def __init__(self, group=None, name=None, value=None, migrate=False):
        if migrate:
            return

        self.var_group = unicode(group)
        self.var_name = unicode(name)

        self.set_v(value)

    @staticmethod
    def find_descriptor(config_desc_root, var_group, var_name):
        d = config_desc_root.get(var_group, {}).get(var_name, None)
        if d is None:
            raise ValueError('%s.%s descriptor cannot be None' % (var_group, var_name))

        return d

    def set_v(self, val):
        desc = self.find_descriptor(self.cfg_desc, self.var_group, self.var_name)
        if val is None:
            val = desc._type()
        if isinstance(desc, config_desc.Unicode) and isinstance(val, str):
            val = unicode(val)
        if not isinstance(val, desc._type):
            raise ValueError("Cannot assign %s with %s" % (self, type(val)))
        if desc.validator is not None:
            desc.validator(self, self.var_name, val)

        if self.value is None:
            self.value = {'v': val}

        elif self.value['v'] != val:
            self.customized = True
            self.value = {'v': val}

    def get_v(self):
        return self.value['v']

    def __repr__(self):
        return "<Config: %s.%s>" % (self.var_group, self.var_name)


class ConfigL10N_v_36(Storm):
    __storm_table__ = 'config_l10n'
    __storm_primary__ = ('lang', 'var_group', 'var_name')

    lang = Unicode()
    var_group = Unicode()
    var_name = Unicode()
    value = Unicode()
    customized = Bool(default=False)

    def __init__(self, lang_code=None, group=None, var_name=None, value='', migrate=False):
        if migrate:
            return

        self.lang = unicode(lang_code)
        self.var_group = unicode(group)
        self.var_name = unicode(var_name)
        self.value = unicode(value)


    def set_v(self, value):
        value = unicode(value)
        if self.value != value:
            self.value = value
            self.customized = True

class Counter_v_36(Model):
    __storm_table__ = 'counter'

    key = Unicode(primary=True, validator=shorttext_v)
    counter = Int(default=1)
    update_date = DateTime(default_factory=datetime_now)


class ShortURL_v_36(ModelWithID):
    __storm_table__ = 'shorturl'
    shorturl = Unicode(validator=shorturl_v)
    longurl = Unicode(validator=longurl_v)


class Context_v_36(ModelWithID):
    __storm_table__ = 'context'
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
    name = JSON(validator=shortlocal_v)
    description = JSON(validator=longlocal_v)
    recipients_clarification = JSON(validator=longlocal_v)
    status_page_message = JSON(validator=longlocal_v)
    show_receivers_in_alphabetical_order = Bool(default=False)
    presentation_order = Int(default=0)
    questionnaire_id = Unicode()
    img_id = Unicode()


class CustomTexts_v_36(Model):
    __storm_table__ = 'customtexts'
    lang = Unicode(primary=True, validator=shorttext_v)
    texts = JSON()


class EnabledLanguage_v_36(Model):
    __storm_table__ = 'enabledlanguage'

    name = Unicode(primary=True)

    @classmethod
    def list(cls, store):
        return [e.name for e in store.find(cls)]


class Field_v_36(ModelWithID):
    __storm_table__ = 'field'
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
    stats_enabled = Bool(default=False)
    triggered_by_score = Int(default=0)
    step_id = Unicode()
    fieldgroup_id = Unicode()
    template_id = Unicode()
    type = Unicode(default=u'inputbox')
    instance = Unicode(default=u'instance')
    editable = Bool(default=True)


class File_v_36(ModelWithID):
    __storm_table__ = 'file'
    data = Unicode()


class IdentityAccessRequest_v_36(ModelWithID):
    __storm_table__ = 'identityaccessrequest'
    receivertip_id = Unicode()
    request_date = DateTime(default_factory=datetime_now)
    request_motivation = Unicode(default=u'')
    reply_date = DateTime(default_factory=datetime_null)
    reply_user_id = Unicode()
    reply_motivation = Unicode(default=u'')
    reply = Unicode(default=u'pending')


class Questionnaire_v_36(ModelWithID):
    __storm_table__ = 'questionnaire'
    key = Unicode(default=u'')
    name = Unicode()
    show_steps_navigation_bar = Bool(default=False)
    steps_navigation_requires_completion = Bool(default=False)
    enable_whistleblower_identity = Bool(default=False)
    editable = Bool(default=True)


class ShortURL_v_36(ModelWithID):
    __storm_table__ = 'shorturl'
    shorturl = Unicode(validator=shorturl_v)
    longurl = Unicode(validator=longurl_v)


class MigrationScript(MigrationBase):
    def generic_migration_function(self, model_name):
        old_objects = self.store_old.find(self.model_from[model_name])

        for old_obj in old_objects:
            new_obj = self.model_to[model_name](migrate=True)

            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'tid' and model_name in ['Config', 'ConfigL10N', 'CustomTexts', 'File', 'ShortUrl']:
                    new_obj.tid = ROOT_TENANT
                else:
                    self.migrate_model_key(old_obj, new_obj, v.name)

            self.store_new.add(new_obj)

    def migrate_Field(self):
        old_objs = self.store_old.find(self.model_from['Field'])
        for old_obj in old_objs:
            new_obj = self.model_to['Field']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'question_id':
                    if old_obj.step_id is None and old_obj.fieldgroup_id is None:
                        qt = self.model_to['Question']()
                        self.store_new.add(qt)
                        new_obj.question_id = qt.id

                        self.store_new.add(self.model_to['Question_Tenant']({
                            'question_id': qt.id,
                            'tenant_id': ROOT_TENANT
                        }))

                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_File(self):
        old_objs = self.store_old.find(self.model_from['File'])
        for old_obj in old_objs:
            new_obj = self.model_to['File']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'tid':
                    new_obj.tid = ROOT_TENANT
                elif v.name == 'key':
                    new_obj.key = old_obj.id
                else:
                    setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def epilogue(self):
        self.store_new.add(tenant.Tenant({'label': 'antani'}))
