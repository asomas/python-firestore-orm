from fields import *
from firebase_admin import firestore, auth
from google.cloud.firestore_v1.document import DocumentReference


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
            raise ValueError(
                f'If subclassing a document, document must have @collection annotation'
            )
        self._set_id(None)

    def _set_id(self, val):
        self.doc_ref = val

    def firestore_raw(self):
        return self._firestore_data

    def _init_document(cls, collection_name):
        cls._firestore_meta = FirestoreMeta(collection_name)
        cls.containing_cls = None
        for (name, schema_name, field) in Map._get_fields_cls(cls):
            field._init_fields(schema_name or name, cls)

    def validate(self):
        class Temp:
            _firestore_data = {'default': self._firestore_data}

        self._validate(Temp)

    @staticmethod
    def _create_from_snapshot(subcls, snapshot):
        obj = subcls()
        obj._firestore_data = snapshot.to_dict()
        obj._set_id(DocRef(subcls, id=snapshot.id))
        obj.validate()
        return obj

    def store(self):
        self.validate()
        if not hasattr(self, 'doc_ref'):
            self.doc_ref = None
        if self.doc_ref is None:
            self.doc_ref = DocRef(type(self))
        self.doc_ref._doc_ref_internal.set(self._firestore_data, merge=True)


def collection(*, name=None):
    def collection_impl(cls):

        Document._init_document(cls, name or cls.__name__)
        return cls

    return collection_impl


class DocRef(Field):
    def __init__(self,
                 cls,
                 *,
                 id=None,
                 rename=None,
                 allow_missing=False,
                 allow_null=False):
        global _firestore_internal_db
        if not issubclass(cls, Document):
            raise ValueError(
                f'DocRef must take an object that inherits Document')
        super().__init__(firestore_type=DocumentReference,
                         schema_name=rename,
                         allow_missing=allow_missing,
                         allow_null=allow_null)
        self._doc_type = cls
        if id != None:
            self._doc_ref_internal = _firestore_internal_db.collection(
                cls._firestore_meta.path()).document(id)
        else:
            self._doc_ref_internal = _firestore_internal_db.collection(
                cls._firestore_meta.path()).document()

    def get(self):
        snapshot = self._doc_ref_internal.get()
        if snapshot.to_dict() is None:
            return None
        return self._doc_type._create_from_snapshot(self._doc_type, snapshot)


def init_orm(*, project, credentials):
    global _firestore_internal_db
    _firestore_internal_db = firestore.Client(project=project,
                                              credentials=credentials)
