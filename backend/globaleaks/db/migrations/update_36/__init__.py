# -*- coding: UTF-8

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import *
from globaleaks.db.migrations.update_37.config import NodeFactory

from urlparse import urlparse


def add_config(store, model_class, group, name, customized, value):
    c = model_class(migrate=True)
    c.var_group = group
    c.var_name =  name
    c.customixed = customized
    c.value = {'v': value}
    store.add(c)


def del_config(store, model_class, group, name):
    store.find(model_class, var_group = group, var_name = name).remove()


class MigrationScript(MigrationBase):
    def epilogue(self):
        nf = NodeFactory(self.store_new)
        nf.model_class = self.model_from['Config']
        url = nf.get_val('public_site')
        o = urlparse(url)
        domain = o.hostname if not o.hostname is None else ''

        del_config(self.store_new, self.model_from['Config'], u'node', u'public_site')
        add_config(self.store_new, self.model_from['Config'], u'node', u'hostname', domain != '', unicode(domain))

        url = nf.get_val('hidden_service')
        o = urlparse(url)
        domain = o.hostname if not o.hostname is None else ''

        del_config(self.store_new, self.model_from['Config'], u'node', u'hidden_service')
        add_config(self.store_new, self.model_from['Config'], u'node', u'onionservice', domain != '', unicode(domain))

        add_config(self.store_new, self.model_from['Config'], u'node', u'reachable_via_web', False, False)
        self.entries_count['Config'] += 1

        self.store_new.commit()
