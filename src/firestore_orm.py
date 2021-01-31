from fields import *
from firebase_admin import firestore, auth
from google.cloud.firestore_v1.document import DocumentReference


class FirestoreMeta:
    """A bit basic for now, until sub collections are added"""
    def __init__(self, *, col_name, key_name):
        self.name = col_name
        self.key_name = key_name

    def path(self):
        return self.name


class Document(Map):
    def __init__(self, *, allow_missing=False, allow_null=False, parse_missing_as_None=False):
        if type(self) == Document:
            raise typeerror(
                'Must subclass Document, Document cannot be created directly.')
        super().__init__(rename=None,
                         allow_missing=allow_missing,
                         allow_null=allow_null, parse_missing_as_None=parse_missing_as_None)
        self.containing_cls = None
        if not hasattr(type(self), '_firestore_meta'):
            raise ValueError(
                f'When subclassing a document, document must have @collection annotation'
            )
        self._set_id(DocRef(type(self)))

    def _set_id(self, val):
        setattr(self, type(self)._firestore_meta.key_name, val)

    def _get_id(self):
        key_name = type(self)._firestore_meta.key_name
        return getattr(self, key_name) if hasattr(self, key_name) else None

    def _init_document(cls, *, col_name, key_name):
        cls._firestore_meta = FirestoreMeta(col_name=col_name,
                                            key_name=key_name)
        cls._firestore_fields = FirestoreFields()
        to_delete = set()
        for (name, schema_name, field) in Document._get_fields(cls):
            if name == key_name or schema_name == key_name:
                raise ValueError(
                    f'Found a field with name {name}, this name cannot be used as it is set as the key_name for {cls.__name__}. To change the key_name, use the key_name parameter to the @collection() annotation.'
                )
            field._init_fields(schema_name or name, cls)
            setattr(cls._firestore_fields, name, field)
            to_delete.add(name)
        for name in to_delete:
            delattr(cls, name)

    @staticmethod
    def _validate_dict(cls, val):
        for (name, schema_name, field) in Document._get_fields(cls._firestore_fields):
            if schema_name not in val:
                if field._allow_missing:
                    continue
                else:
                    raise ValidatorException(
                        f'field "{schema_name}" is missing.')
            field._validate_dict(val[schema_name])

    def to_dict(self):
        dict_ = Map.python_to_dict(type(self), self)
        dict_.pop(type(self)._firestore_meta.key_name, None)
        Document._validate_dict(type(self), dict_)
        return dict_

    @staticmethod
    def from_dict(subcls, dict_in):
        subcls._validate_dict(subcls, dict_in)
        return subcls.dict_to_python(subcls, dict_in)

    def store(self, doc_ref_or_str_id=None):
        dict_ = self.to_dict()
        dr = doc_ref_or_str_id
        if dr is not None:
            dr = dr if type(dr) == DocRef else DocRef(type(self), id=dr)
            self._set_id(dr)
        self._get_id()._doc_ref_internal.set(dict_, merge=True)

    @staticmethod
    def get(cls, doc_ref_or_id_str):
        doc_ref = doc_ref_or_id_str if type(
            doc_ref_or_id_str) == DocRef else DocRef(cls, id=doc_ref_or_id_str)
        snapshot = doc_ref._doc_ref_internal.get()
        dict_json = snapshot.to_dict()
        if dict_json is None:
            return None
        obj = cls.from_dict(cls, dict_json)
        obj._set_id(doc_ref)
        return obj


def collection(*, name=None, key_name='doc_ref'):
    def collection_impl(cls):

        Document._init_document(cls,
                                col_name=name or cls.__name__,
                                key_name=key_name)
        return cls

    return collection_impl


class DocRef(Field):
    def __init__(self,
                 cls,
                 *,
                 id=None,
                 rename=None,
                 allow_missing=False,
                 allow_null=False, parse_missing_as_None=False):
        global _firestore_internal_db
        if not issubclass(cls, Document):
            raise ValueError(
                f'DocRef must take an object that inherits Document')
        super().__init__(firestore_type=DocumentReference,
                         schema_name=rename,
                         allow_missing=allow_missing,
                         allow_null=allow_null, parse_missing_as_None=parse_missing_as_None)
        self._doc_type = cls
        if id != None:
            self._doc_ref_internal = _firestore_internal_db.collection(
                cls._firestore_meta.path()).document(id)
        else:
            self._doc_ref_internal = _firestore_internal_db.collection(
                cls._firestore_meta.path()).document()

    def get(self):
        return self._doc_type.get(self._doc_type, self)


def init_orm(*, project, credentials):
    global _firestore_internal_db
    _firestore_internal_db = firestore.Client(project=project,
                                              credentials=credentials)
