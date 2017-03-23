# -*- coding: UTF-8

from storm.locals import Bool, Int, Reference, ReferenceSet, Unicode, Storm, JSON


from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models.validators import shorttext_v, longtext_v, \
    shortlocal_v, longlocal_v, shorturl_v, longurl_v, natnum_v, range_v
from globaleaks.models import *
from globaleaks.utils.utility import datetime_now

from urlparse import urlparse

class Config_v_36(Model):
    __storm_table__ = 'config'
    __storm_primary__ = ('var_group', 'var_name')

    var_group = Unicode()
    var_name = Unicode()
    value = JSON()
    customized = Bool(default=False)

    def __init__(self, group=None, name=None, value=None, cfg_desc=None, migrate=False):
        """
        :param value:    This input is passed directly into set_v
        :param migrate:  Added to comply with models.Model constructor which is
                         used to copy every field returned by storm from the db
                         from an old_obj to a new one.
        :param cfg_desc: Used to specify where to look for the Config objs descripitor.
                         This is used in mig 34.
        """
        if cfg_desc is not None:
            self.cfg_desc = cfg_desc

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



class MigrationScript(MigrationBase):
    def generic_migration_function(self, model_name):
        old_objects = self.store_old.find(self.model_from[model_name])

        for old_obj in old_objects:
            new_obj = self.model_to[model_name](migrate=True)

            for _, v in new_obj._storm_columns.iteritems():
                self.migrate_model_key(old_obj, new_obj, v.name)

                if v.name == 'tid' and model_name == 'Config':
                    new_obj.tid = 0
                    print "ok"

            self.store_new.add(new_obj)
