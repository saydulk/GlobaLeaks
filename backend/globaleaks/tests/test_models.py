#  -*- coding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks

from globaleaks import models, LANGUAGES_SUPPORTED
from globaleaks.constants import FIRST_TENANT
from globaleaks.db.appdata import load_appdata
from globaleaks.handlers.admin.questionnaire import db_get_default_questionnaire_id
from globaleaks.models import config
from globaleaks.models.config_desc import GLConfig
from globaleaks.models.l10n import NodeL10NFactory, NotificationL10NFactory, EnabledLanguage, ConfigL10N
from globaleaks.orm import transact
from globaleaks.tests import helpers


class TestSystemConfigModels(helpers.TestGL):
    @transact
    def _test_config_import(self, store):
        c = store.find(config.Config, tid=FIRST_TENANT).count()

        stated_conf = reduce(lambda x,y: x+y, [len(v) for k, v in GLConfig.iteritems()], 0)
        self.assertEqual(c, stated_conf)

    @inlineCallbacks
    def test_config_import(self):
        yield self._test_config_import()

    @transact
    def _test_valid_cfg(self, store):
        self.assertEqual(True, config.is_cfg_valid(store, FIRST_TENANT))

    @inlineCallbacks
    def test_valid_config(self):
        yield self._test_valid_cfg()

    @transact
    def _test_missing_config(self, store):
        self.assertEqual(True, config.is_cfg_valid(store, FIRST_TENANT))

        p = config.Config(FIRST_TENANT, 'private', 'smtp_password', 'XXXX')
        p.var_group = u'outside'
        store.add(p)

        self.assertEqual(False, config.is_cfg_valid(store, FIRST_TENANT))

        node = config.NodeFactory(store, FIRST_TENANT)
        c = node.get_cfg('hostname')
        store.remove(c)
        store.commit()

        self.assertEqual(False, node.db_corresponds())

        # Delete all of the vars in Private Factory
        prv = config.PrivateFactory(store, FIRST_TENANT)

        store.execute('DELETE FROM config WHERE var_group = "private"')

        self.assertEqual(False, prv.db_corresponds())

        ntfn = config.NotificationFactory(store, FIRST_TENANT)

        c = config.Config(FIRST_TENANT, 'notification', 'server', 'guarda.giochi.con.occhi')
        c.var_name = u'anextravar'
        store.add(c)

        self.assertEqual(False, ntfn.db_corresponds())

        config.update_defaults(store, FIRST_TENANT)

        self.assertEqual(True, config.is_cfg_valid(store, FIRST_TENANT))

    @inlineCallbacks
    def test_missing_config(self):
        yield self._test_missing_config()


class TestConfigL10N(helpers.TestGL):
    @transact
    def enable_langs(self, store):
        appdata = load_appdata()

        key_num = 0
        for key in GLConfig:
            key_num += len(GLConfig[key].keys())

        key_num = len(NodeL10NFactory.localized_keys) + len(NotificationL10NFactory.localized_keys)

        res = EnabledLanguage.list(store, FIRST_TENANT)
        self.assertTrue(len(res) == 1)
        self.assertTrue([u'en'] == res)
        self.assertTrue(store.find(ConfigL10N, tid=FIRST_TENANT).count() == key_num)

        EnabledLanguage.enable_language(store, FIRST_TENANT, u'ar', appdata)

        res = EnabledLanguage.list(store, FIRST_TENANT)
        self.assertTrue(len(res) == 2)
        self.assertTrue([u'ar', 'en'] == res)
        self.assertTrue(store.find(ConfigL10N, tid=FIRST_TENANT).count() == key_num * 2)

    @transact
    def disable_langs(self, store):
        EnabledLanguage.disable_language(store, FIRST_TENANT, u'en')

        res = EnabledLanguage.list(store, FIRST_TENANT)
        self.assertTrue(len(res) == 0)
        self.assertTrue(store.find(ConfigL10N, tid=FIRST_TENANT).count() == 0)

    @inlineCallbacks
    def test_enabled_langs(self):
        yield self.enable_langs()

    @inlineCallbacks
    def test_disable_langs(self):
        yield self.disable_langs()


class TestModels(helpers.TestGL):
    receiver_inc = 0

    @transact
    def context_add(self, store):
        c = self.localization_set(self.dummyContext, models.Context, 'en')
        context = models.Context(c)
        context.tid = FIRST_TENANT
        context.questionnaire_id = db_get_default_questionnaire_id(store)
        context.tip_timetolive = 1000
        context.description = context.name = \
            context.submission_disclaimer = \
            context.submission_introduction = {'en': 'Localized723'}
        store.add(context)
        return context.id

    @transact
    def receiver_add(self, store):
        u = self.localization_set(self.dummyReceiverUser_1, models.User, 'en')
        receiver_user = models.User(u)
        receiver_user.mail_address = self.dummyReceiverUser_1['mail_address']
        receiver_user.username = str(
            self.receiver_inc) + self.dummyReceiver_1['mail_address']
        receiver_user.password = self.dummyReceiverUser_1['password']
        receiver_user.salt = self.dummyReceiverUser_1['salt']
        store.add(receiver_user)

        r = self.localization_set(self.dummyReceiver_1, models.Receiver, 'en')
        receiver = models.Receiver(r)
        receiver.user = receiver_user
        receiver.user.pgp_key_expiration = "1970-01-01 00:00:00.000000"
        receiver.user.pgp_key_fingerprint = ""
        receiver.user.pgp_key_public = ""

        receiver.mail_address = self.dummyReceiver_1['mail_address']

        store.add(receiver)

        self.receiver_inc += 1

        return receiver.id

    @transact
    def create_context_with_receivers(self, store):
        u1 = self.localization_set(self.dummyReceiverUser_1, models.User, 'en')
        receiver_user1 = models.User(u1)
        receiver_user1.password = self.dummyReceiverUser_1['password']
        receiver_user1.salt = self.dummyReceiverUser_1['salt']

        u2 = self.localization_set(self.dummyReceiverUser_2, models.User, 'en')
        receiver_user2 = models.User(u2)
        receiver_user2.password = self.dummyReceiverUser_2['password']
        receiver_user2.salt = self.dummyReceiverUser_2['salt']

        store.add(receiver_user1)
        store.add(receiver_user2)

        c = self.localization_set(self.dummyContext, models.Context, 'en')
        context = models.Context(c)
        context.tid = FIRST_TENANT
        context.questionnaire_id = db_get_default_questionnaire_id(store)
        context.tip_timetolive = 1000
        context.description = context.name = \
            context.submission_disclaimer = \
            context.submission_introduction = {'en': 'Localized76w'}

        r1 = self.localization_set(self.dummyReceiver_1, models.Receiver, 'en')
        r2 = self.localization_set(self.dummyReceiver_2, models.Receiver, 'en')
        receiver1 = models.Receiver(r1)
        receiver2 = models.Receiver(r2)

        receiver1.user = receiver_user1
        receiver2.user = receiver_user2

        receiver1.user.pgp_key_expiration = "1970-01-01 00:00:00.000000"
        receiver1.user.pgp_key_fingerprint = ""
        receiver1.user.pgp_key_public = ""

        receiver2.user.pgp_key_expiration = "1970-01-01 00:00:00.000000"
        receiver2.user.pgp_key_fingerprint = ""
        receiver2.user.pgp_key_public = ""

        receiver1.mail_address = 'x@x.it'
        receiver2.mail_address = 'x@x.it'

        context.receivers.add(receiver1)
        context.receivers.add(receiver2)

        store.add(context)

        return context.id

    @transact
    def create_receiver_with_contexts(self, store):
        c = self.localization_set(self.dummyContext, models.Context, 'en')
        r = self.localization_set(self.dummyReceiver_1, models.Receiver, 'en')

        u = self.localization_set(self.dummyReceiverUser_1, models.User, 'en')
        receiver_user = models.User(u)
        # Avoid receivers with the same username!
        receiver_user.username = u'xxx'
        receiver_user.password = self.dummyReceiverUser_1['password']
        receiver_user.salt = self.dummyReceiverUser_1['salt']
        store.add(receiver_user)

        receiver = models.Receiver(r)
        receiver.user = receiver_user
        receiver.user.pgp_key_expiration = "1970-01-01 00:00:00.000000"
        receiver.user.pgp_key_fingerprint = ""
        receiver.user.pgp_key_public = ""
        receiver.mail_address = u'y@y.it'

        context1 = models.Context(c)
        context1.questionnaire_id = db_get_default_questionnaire_id(store)
        context1.tip_timetolive = 1000
        context1.description = context1.name = \
            context1.submission_disclaimer = \
            context1.submission_introduction = {'en': 'Valar Morghulis'}

        context2 = models.Context(c)
        context2.questionnaire_id = db_get_default_questionnaire_id(store)
        context2.tip_timetolive = 1000
        context2.description = context2.name = \
            context2.submission_disclaimer = \
            context2.submission_introduction = {'en': 'Valar Dohaeris'}

        receiver.contexts.add(context1)
        receiver.contexts.add(context2)
        store.add(receiver)
        return receiver.id

    @transact
    def list_receivers_of_context(self, store, context_id):
        context = models.Context.db_get(store, id=context_id)
        return [r.id for r in context.receivers]

    @transact
    def list_context_of_receivers(self, store, receiver_id):
        """
        Return the list of context ids associated with the receiver identified
        by receiver_id.
        """
        receiver = models.Receiver.db_get(store, id=receiver_id)
        return [c.id for c in receiver.contexts]

    @inlineCallbacks
    def test_context_add_and_get(self):
        context_id = yield self.context_add()
        check = yield models.Context.test(id=context_id)
        self.assertTrue(check)

    @inlineCallbacks
    def test_context_add_and_del(self):
        context_id = yield self.context_add()
        yield models.Context.delete(id=context_id)
        check = yield models.Context.test(id=context_id)
        self.assertFalse(check)

    @inlineCallbacks
    def test_receiver_add_and_get(self):
        receiver_id = yield self.receiver_add()
        check = yield models.Receiver.test(id=receiver_id)
        self.assertTrue(check)

    @inlineCallbacks
    def test_receiver_add_and_del(self):
        receiver_id = yield self.receiver_add()
        yield models.Receiver.delete(id=receiver_id)
        check = yield models.Receiver.test(id=receiver_id)
        self.assertFalse(check)

    @inlineCallbacks
    def test_context_receiver_reference_1(self):
        context_id = yield self.create_context_with_receivers()
        yield self.assert_model_exists(models.Context, id=context_id)
        receivers = yield self.list_receivers_of_context(context_id)
        self.assertEqual(2, len(receivers))

    @inlineCallbacks
    def test_context_receiver_reference_2(self):
        receiver_id = yield self.create_receiver_with_contexts()
        yield self.assert_model_exists(models.Receiver, id=receiver_id)
        contexts = yield self.list_context_of_receivers(receiver_id)
        self.assertEqual(2, len(contexts))


class TestField(helpers.TestGL):
    @inlineCallbacks
    def setUp(self):
        yield super(TestField, self).setUp()

    @transact
    def add_children(self, store, field_id, *field_ids):
        parent = models.Field.db_get(store, id=field_id)
        for field_id in field_ids:
            field = models.Field.db_get(store, id=field_id)
            parent.children.add(field)

    @transact
    def get_children(self, store, field_id):
        return [c.id for c in models.Field.db_get(store, id=field_id).children]

    @inlineCallbacks
    def test_field(self):
        field1_id = yield self.create_dummy_field()
        yield self.assert_model_exists(models.Field, id=field1_id)

        field2_id = yield self.create_dummy_field(type='checkbox')
        yield self.assert_model_exists(models.Field, id=field2_id)

        yield models.Field.delete(id=field1_id)
        yield self.assert_model_not_exists(models.Field, id=field1_id)
        yield self.assert_model_exists(models.Field, id=field2_id)
