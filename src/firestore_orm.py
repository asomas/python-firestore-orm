from fields import *


class FirestoreMeta:
    def __init__(self, *, parent_path, name):
        self.parent_path = parent_path
        self.name = name
    def path(self):
        return self.parent_path + self.name


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
            type(self)._firestore_meta = FirestoreMeta(name=None,
                                                       parent_path='')
        if type(self)._firestore_meta.name is None:
            type(self)._firestore_meta.name = type(self).__name__

    def validate(self):
        class Temp:
            _firestore_data = {'default': self._firestore_data}

        self._validate(Temp)


def collection(*, name=None, parent=''):
    def collection_impl(cls):
        if parent is None:
            path = ''
        elif type(parent) == str:
            path = parent
        elif issubclass(parent, Document):
            path = parent._firestore_meta.path() + '/' if hasattr(parent, '_firestore_meta') else parent.__name__ + '/'
        cls._firestore_meta = FirestoreMeta(name=name or cls.__name__, parent_path=path)
        return cls
    return collection_impl


class Worker(Document):
    pass


@collection(name='public', parent=Worker)
class WorkerPublic(Document):
    pass


print(WorkerPublic._firestore_meta.path())
