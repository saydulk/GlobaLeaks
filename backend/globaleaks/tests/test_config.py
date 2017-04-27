#  -*- coding: utf-8 -*-

from twisted.internet.defer import inlineCallbacks

from globaleaks import LANGUAGES_SUPPORTED
from globaleaks.state import app_state
from globaleaks.db.appdata import load_appdata
from globaleaks.handlers.admin.questionnaire import db_get_default_questionnaire_id
from globaleaks.models import config
from globaleaks.models import Context
from globaleaks.models.config_desc import GLConfig
from globaleaks.models.l10n import NodeL10NFactory, NotificationL10NFactory, EnabledLanguage, ConfigL10N
from globaleaks.orm import transact
from globaleaks.tests import helpers

class TestSystemConfigModels(helpers.TestGL):
    @transact
    def _test_config_import(self, store):
        c = store.find(config.Config, tid=app_state.root_id).count()

        stated_conf = reduce(lambda x,y: x+y, [len(v) for k, v in GLConfig.iteritems()], 0)
        self.assertEqual(c, stated_conf)

    @inlineCallbacks
    def test_config_import(self):
        yield self._test_config_import()

    @transact
    def _test_valid_cfg(self, store):
        self.assertEqual(True, config.is_cfg_valid(store, app_state.root_id))

    @inlineCallbacks
    def test_valid_config(self):
        yield self._test_valid_cfg()

    @transact
    def _test_missing_config(self, store):
        self.assertEqual(True, config.is_cfg_valid(store, app_state.root_id))

        p = config.Config(app_state.root_id, 'private', 'smtp_password', 'XXXX')
        p.var_group = u'outside'
        store.add(p)

        self.assertEqual(False, config.is_cfg_valid(store, app_state.root_id))

        node = config.NodeFactory(store, app_state.root_id)
        c = node.get_cfg('hostname')
        store.remove(c)
        store.commit()

        self.assertEqual(False, node.db_corresponds())

        # Delete all of the vars in Private Factory
        prv = config.PrivateFactory(store, app_state.root_id)

        store.execute('DELETE FROM config WHERE var_group = "private"')

        self.assertEqual(False, prv.db_corresponds())

        ntfn = config.NotificationFactory(store, app_state.root_id)

        c = config.Config(app_state.root_id, 'notification', 'server', 'guarda.giochi.con.occhi')
        c.var_name = u'anextravar'
        store.add(c)

        self.assertEqual(False, ntfn.db_corresponds())

        config.update_defaults(store, app_state.root_id)

        self.assertEqual(True, config.is_cfg_valid(store, app_state.root_id))

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

        res = EnabledLanguage.list(store, app_state.root_id)
        self.assertTrue(len(res) == 1)
        self.assertTrue([u'en'] == res)
        self.assertTrue(store.find(ConfigL10N, tid=app_state.root_id).count() == key_num)

        EnabledLanguage.enable_language(store, app_state.root_id, u'ar', appdata)

        res = EnabledLanguage.list(store, app_state.root_id)
        self.assertTrue(len(res) == 2)
        self.assertTrue([u'ar', 'en'] == res)
        self.assertTrue(store.find(ConfigL10N, tid=app_state.root_id).count() == key_num * 2)

    @transact
    def disable_langs(self, store):
        EnabledLanguage.disable_language(store, app_state.root_id, u'en')

        res = EnabledLanguage.list(store, app_state.root_id)
        self.assertTrue(len(res) == 0)
        self.assertTrue(store.find(ConfigL10N, tid=app_state.root_id).count() == 0)

    @inlineCallbacks
    def test_enabled_langs(self):
        yield self.enable_langs()

    @inlineCallbacks
    def test_disable_langs(self):
        yield self.disable_langs()
