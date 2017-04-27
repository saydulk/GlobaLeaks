from globaleaks.constants import ROOT_TENANT
from globaleaks.utils.tor_exit_set import TorExitSet
from globaleaks import LANGUAGES_SUPPORTED_CODES, models
from globaleaks.orm import transact, transact_sync
from globaleaks.settings import GLSettings
from globaleaks.utils.objectdict import ObjectDict


class TenantState(object):
    def __init__(self, store, tid):
        self.id = tid
        self.memc = ObjectDict()

        self.db_refresh(store)

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
        return self.db_refresh(store)

    def __repr__(self):
        return '<TenantState %s, %s>' % (self.id, self.memc.https_hostname)


class AppState(object):
    def __init__(self):
        self.process_supervisor = None

        self.tor_exit_set = TorExitSet()
        self.jobs = []
        self.jobs_monitor = None

        self.defaults = ObjectDict({
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

        self.root_id = ROOT_TENANT
        self.tenant_states = dict()
        self.tenant_hostname_id_map = dict()

    def db_refresh(self, store):
        tenants = store.find(models.Tenant, models.Tenant.active == True)
        self.tenant_hostname_id_map = {t.https_hostname: t.id for t in tenants}
        if GLSettings.devel_mode:
            for t in tenants:
                dummy_https_hname = t.https_hostname.split(':')[0] + ':9443'
                self.tenant_hostname_id_map[dummy_https_hname] = t.id

        tenants_ids = [t.id for t in tenants]

        to_remove = set(self.tenant_states.keys()) - set(tenants_ids)

        for k in to_remove:
            del self.tenant_states[k]

        for tid in tenants_ids:
            if tid not in self.tenant_states:
                self.tenant_states[tid] = TenantState(store, tid)
            else:
                self.tenant_states[tid].db_refresh(store)

        self.memc = self.tenant_states[self.root_id].memc

        # TODO reenable excep list generation
        #self.db_refresh_exception_delivery_list(store)

    def db_refresh_exception_delivery_list(self, store):
        """
        Constructs a list of (email_addr, public_key) pairs that will receive errors from the platform.
        If the email_addr is empty, drop the tuple from the list.
        """
        notif_fact = models.config.NotificationFactory(store, ROOT_TENANT)
        error_addr = notif_fact.get_val('exception_email_address')
        error_pk = notif_fact.get_val('exception_email_pgp_key_public')

        lst = [(error_addr, error_pk)]

        results = store.find(models.User, models.User.role == unicode('admin'),
                                          models.User.id == models.User_Tenant.user_id,
                                          models.Tenant.id == ROOT_TENANT
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
        return self.tenant_states[ROOT_TENANT]


app_state = AppState()
