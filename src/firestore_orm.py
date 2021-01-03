from fields import *


class FirestoreMeta:
    """A bit basic for now, until sub collections are added"""
    def __init__(self, name):
        self.name = name
    def path(self):
        return self.name


class Document(Map):
    def __init__(self,
                 *,
                 rename='default',
                 allow_missing=False,
                 allow_null=False):
        if type(self) == Document:
            raise typeerror(
                'Must subclass Document, Document cannot be created directly.')
        super().__init__(rename=rename,
                         allow_missing=allow_missing,
                         allow_null=allow_null)
        if not hasattr(type(self), '_firestore_meta'):
            raise ValueError(f'If subclassing a document, document must have @collection annotation')
    def firestore_raw(self):
        return self._firestore_data
        
    def _init_document(cls, collection_name):
        cls._firestore_meta = FirestoreMeta(collection_name)
        cls.containing_cls = None
        for (name,schema_name,field) in Map._get_fields_cls(cls):
            field._init_fields(schema_name or name, cls)
        
    def validate(self):
        class Temp:
            _firestore_data = {'default': self._firestore_data}

        self._validate(Temp)


def collection(*, name=None):
    def collection_impl(cls):
        
        Document._init_document(cls, name or cls.__name__)
        return cls
    return collection_impl






class Db:
    def __init__(self, *, project, credentials):
        self.db = firestore.Client(project=project, credentials=credentials)
    def put(self, item, *, id=None):
        if not isinstance(item, Document):
            raise typeerror(f'Expected subclass of Document but found {type(item)}')
        item.validate()
        self.db.collection(item._firestore_meta.path()).add(item.firestore_raw())
