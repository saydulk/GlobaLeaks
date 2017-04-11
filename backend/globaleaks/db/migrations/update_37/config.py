from storm.expr import And, Not
from storm.locals import Storm, Bool, Unicode, JSON

from globaleaks import __version__
from globaleaks.utils.utility import log

import config_desc
from .config_desc import GLConfig


class ConfigFactory(object):
    """
    This factory depends on the following attributes set by the sub class:
    """
    update_set = frozenset() # keys updated when fact.update(d) is called
    group_desc = dict() # the corresponding dict in GLConfig

    def __init__(self, group, store, lazy=True, *args, **kwargs):
        self.group = unicode(group)
        self.store = store
        self.res = None
        if not lazy:
            self._query_group()

    def _query_group(self):
        if self.res is not None:
            return

        cur = self.store.find(Config, And(Config.var_group == self.group))
        self.res = {c.var_name: c for c in cur}

    def get_cfg(self, var_name):
        if self.res is None:
            where = And(Config.var_group == self.group, Config.var_name == unicode(var_name))
            r = self.store.find(Config, where).one()
            if r is None:
                raise KeyError("No such config item: %s:%s" % (self.group, var_name))
            return r
        else:
            return self.res[var_name]

    def get_val(self, var_name):
        return self.get_cfg(var_name).get_v()


class NodeFactory(ConfigFactory):
    node_private_fields = frozenset({
        'basic_auth',
        'basic_auth_username',
        'basic_auth_password',
        'default_password',
        'default_timezone',

        'can_postpone_expiration',
        'can_delete_submission',
        'can_grant_permissions',

        'allow_indexing',

        'threshold_free_disk_megabytes_high',
        'threshold_free_disk_megabytes_medium',
        'threshold_free_disk_megabytes_low',
        'threshold_free_disk_percentage_high',
        'threshold_free_disk_percentage_medium',
        'threshold_free_disk_percentage_low',
    })

    admin_node = frozenset(GLConfig['node'].keys())

    public_node = admin_node - node_private_fields

    update_set = admin_node
    group_desc = GLConfig['node']

    def __init__(self, store, *args, **kwargs):
        ConfigFactory.__init__(self, 'node', store, *args, **kwargs)


class Config(Storm):
    __storm_table__ = 'config'
    __storm_primary__ = ('var_group', 'var_name')

    cfg_desc = GLConfig
    var_group = Unicode()
    var_name = Unicode()
    value = JSON()
    customized = Bool(default=False)

    def __init__(self, group=None, name=None, value=None, migrate=False):
        pass

    def get_v(self):
        return self.value['v']
