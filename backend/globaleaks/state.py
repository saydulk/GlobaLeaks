from cyclone.util import ObjectDict

from globaleaks.utils.tor_exit_set import TorExitSet
from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks import models
from globaleaks.orm import transact, transact_sync
from globaleaks.settings import GLSettings

# TODO Subclass from dictionary
class State(object):
    def __init__(self):
        self.process_supervisor = None

        self.tor_exit_set = TorExitSet()
        self.jobs = []
        self.jobs_monitor = None

        self.memc = ObjectDict({
            'maximum_namesize': 128,
            'maximum_textsize': 4096,
            'maximum_filesize': 30,
            'allow_iframes_inclusion': False,
            'accept_tor2web_access': {
                'admin': True,
                'whistleblower': False,
                'custodian': False,
                'receiver': False,
                'unauth': True,
            },
            'private': {
                'https_enabled': False,
            },
            'anonymize_outgoing_connections': True,
        })

        self.tenant_states = dict()


    def db_refresh(self, store):
        # TODO Determine first tenant NOTE use ringobingo
        self.root_id = store.find(models.Tenant, id=1).order_by(models.Tenant.id).one().id

        # Initialize tenant state or refresh existing tenant
        db_tenants = list(store.find(models.Tenant))
        self.tenant_label_id_map = {t.label: t.id for t in db_tenants}

        for db_tenant in db_tenants:
            t_state = self.tenant_states.get(db_tenant.id)
            if t_state is None:
                t_state = TenantState(db_tenant.id)
                self.tenant_states[db_tenant.id] = t_state

            t_state.db_refresh(store)

        # Check for t_state objects that are no longer needed
        cur_ten_ids = [db_t.id for db_t in db_tenants]
        tids_to_remove = filter(lambda tid: not tid in cur_ten_ids, self.tenant_states.keys())
        for tid in tids_to_remove:
            self.tenant_states.pop(tid)

        self.db_refresh_root_memc(store)

    def db_refresh_root_memc(self, store):
        # Initialize first tenant memory_copy
        ts = self.tenant_states[self.root_id]
        self.memc = ts.memc

        self.db_refresh_exception_delivery_list(store)

    def db_refresh_exception_delivery_list(self, store):
        """
        Constructs a list of (email_addr, public_key) pairs that will receive errors from the platform.
        If the email_addr is empty, drop the tuple from the list.
        """
        notif_fact = models.config.NotificationFactory(store, self.root_id)
        error_addr = notif_fact.get_val('exception_email_address')
        error_pk = notif_fact.get_val('exception_email_pgp_key_public')

        lst = [(error_addr, error_pk)]

        # TODO Only send exception notification mails. . . root_id is used here.
        results = store.find(models.User, models.User.role ==unicode('admin'),
                                   models.User.id == models.User_Tenant.user_id,
                                   models.Tenant.id == self.root_id,
                            ).values(models.User.mail_address, models.User.pgp_key_public)

        lst.extend([(mail, pub_key) for (mail, pub_key) in results])
        trimmed = filter(lambda x: x[0] != '', lst)
        self.memc.notif.exception_delivery_list = trimmed

    @transact_sync
    def sync_refresh(self, store):
        return self.db_refresh(store)

    @transact
    def refresh(self, store):
        return self.db_refresh(store)

    def get_root_tenant(self):
        return self.tenant_states[self.root_id]

class TenantState(object):
    def __init__(self, tid):
        #TODO self.api_cache = GLApiCache()
        self.id = tid
        self.memc = ObjectDict({})

    def db_refresh(self, store):
        node_ro = ObjectDict(models.config.NodeFactory(store, self.id).admin_export())

        self.memc = node_ro

        self.memc.accept_tor2web_access = {
            'admin': node_ro.tor2web_admin,
            'custodian': node_ro.tor2web_custodian,
            'whistleblower': node_ro.tor2web_whistleblower,
            'receiver': node_ro.tor2web_receiver,
            'unauth': node_ro.tor2web_unauth
        }

        if node_ro['wizard_done']:
            enabled_langs = models.l10n.EnabledLanguage.list(store, self.id)
        else:
            enabled_langs = LANGUAGES_SUPPORTED_CODES

        self.memc.languages_enabled = enabled_langs

        notif_fact = models.config.NotificationFactory(store, self.id)
        notif_ro = ObjectDict(notif_fact.admin_export())

        self.memc.notif = notif_ro

        if GLSettings.developer_name:
            self.memc.notif.source_name = GLSettings.developer_name

        self.memc.private = ObjectDict(models.config.PrivateFactory(store, self.id).mem_copy_export())

    @transact
    def refresh(self, store):
        return db_refresh(self, store)


app_state = State()
