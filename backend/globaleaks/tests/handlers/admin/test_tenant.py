from twisted.internet.defer import inlineCallbacks

from globaleaks.db.appdata import load_appdata
from globaleaks.state import app_state
from globaleaks.handlers.admin import tenant
from globaleaks.handlers.admin.tenant import db_create_tenant 
from globaleaks.state import AppState
from globaleaks.models.config import NodeFactory
from globaleaks.orm import transact

from globaleaks.tests import helpers


class TestStateChanges(helpers.TestGL):
    @inlineCallbacks
    def test_get(self):
        for i in range(3):
            yield tenant.create_tenant({'label': 'tenant-%i' % i, 'active': True}, load_appdata())

    @inlineCallbacks
    def test_delete(self):
        tenant_desc = yield tenant.create_tenant({'label': 'tenant-xxx', 'active': True}, load_appdata())

    @inlineCallbacks
    def test_init_and_refresh_app_state(self):
        yield self.db_test_init_and_refresh_app_state()

    @transact
    def db_test_init_and_refresh_app_state(self, store):
        app_state = AppState()
        app_state.db_refresh(store)

        self.assertEqual(len(app_state.tenant_states), 1)

        # Add another tenant to the system
        new_ten = db_create_tenant(store, {'label': 'tn2.localhost:8082', 'active': True}, load_appdata())

        app_state.db_refresh(store)

        # Modify root_tenant config
        NodeFactory(store, app_state.root_id).set_val('disable_submissions', True)

        app_state.db_refresh(store)

        self.assertTrue(app_state.memc.disable_submissions)
        self.assertEqual(len(app_state.tenant_states), 2)

        for tstate in app_state.tenant_states.values():
            tstate.db_refresh(store)

        app_state.db_refresh_exception_delivery_list(store)

        # Remove the new tenant from the system
        store.remove(new_ten)
        store.flush()

        app_state.db_refresh(store)

        self.assertEqual(len(app_state.tenant_states), 1)
