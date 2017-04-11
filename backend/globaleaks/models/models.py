# -*- coding: UTF-8

from storm.locals import Bool, Int, Reference, ReferenceSet, Unicode, Storm, JSON
from .properties import MetaModel

from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.utils.utility import uuid4


class Model(Storm):
    """
    Globaleaks's most basic model.

    Define a set of methods  on the top of Storm to simplify
    creation/access/update/deletions of data.
    """
    __metaclass__ = MetaModel
    __storm_table__ = None

    # initialize empty list for the base classes
    unicode_keys = []
    localized_keys = []
    int_keys = []
    bool_keys = []
    datetime_keys = []
    json_keys = []

    def __init__(self, values=None, migrate=False):
        if migrate:
            return

        self.update(values)

    def update(self, values=None):
        """
        Updated Models attributes from dict.
        """
        # May raise ValueError and AttributeError
        if values is None:
            return

        keys = getattr(self, 'unicode_keys') + \
               getattr(self, 'int_keys') + \
               getattr(self, 'datetime_keys') + \
               getattr(self, 'bool_keys') + \
               getattr(self, 'localized_keys') + \
               getattr(self, 'json_keys')

        for k in keys:
            if k in values and values[k] != '':
                value = values[k]
                if k in getattr(self, 'unicode_keys'):
                    value = unicode(value)
                elif k in getattr(self, 'int_keys'):
                    value = int(value)
                elif k in getattr(self, 'bool_keys'):
                    if values == u'true':
                        value = True
                    elif value == u'false':
                        value = False
                    value = bool(value)
                elif k in getattr(self, 'localized_keys'):
                    previous = getattr(self, k, {})
                    if previous is not None:
                        previous.update(value)
                        value = previous

                setattr(self, k, value)

    @classmethod
    def db_get(cls, store, *args, **kwargs):
        ret = store.find(cls, *args, **kwargs).one()
        if ret is None:
            raise errors.ModelNotFound(cls)

        return ret

    @classmethod
    @transact
    def test(store, cls, *args, **kwargs):
        try:
            cls.db_get(store, *args, **kwargs)
        except:
            return False

        return True

    @classmethod
    def db_delete(cls, store, *args, **kwargs):
        store.find(cls, *args, **kwargs).remove()

    @classmethod
    @transact
    def delete(store, cls, **kwargs):
        cls.db_delete(store, **kwargs)

    def __str__(self):
        # pylint: disable=no-member
        values = ['{}={}'.format(attr, getattr(self, attr)) for attr in self._public_attrs]
        return '<%s model with values %s>' % (self.__class__.__name__, ', '.join(values))

    def __repr__(self):
        return self.__str__()

    def __setattr__(self, name, value):
        # harder better faster stronger
        if isinstance(value, str):
            value = unicode(value)
        return super(Model, self).__setattr__(name, value)

    def dict(self, *keys):
        """
        Return a dictionary serialization of the current model.
        if no filter is provided, returns every single attribute.

        :raises KeyError: if a key is not recognized as public attribute.
        """
        # pylint: disable=no-member
        keys = set(keys or self._public_attrs)
        not_allowed_keys = keys - self._public_attrs
        if not_allowed_keys:
            raise KeyError('Invalid keys: {}'.format(not_allowed_keys))
        else:
            return {key: getattr(self, key) for key in keys & self._public_attrs}


class ModelWithID(Model):
    """
    Base class for models requiring an ID
    """
    __storm_table__ = None

    id = Unicode(primary=True, default_factory=uuid4)


class ModelWithTID(Model):
    """
    Base class for models requiring a TID
    """
    __storm_table__ = None

    tid = Int(primary=True, default=1)


class ModelWithIDandTID(Model):
    """
    Base class for models requiring a TID and an ID
    """
    __storm_table__ = None

    id = Unicode(primary=True, default_factory=uuid4)
    tid = Int(default=1)
