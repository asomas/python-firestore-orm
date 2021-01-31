import numbers
import copy
SPECIAL_KEYS = {
    '_schema_name', '_allow_missing', '_allow_null', '_containing_instance',
    '_firestore_data'
}


class ValidatorException(Exception):
    def __init__(self, message):
        self.message = message
        self.error_path = []

    def str(self):
        error_path_str = ''.join(
            f'["{segment}"]' if type(segment) == str else f'[{segment}]'
            for segment in self.error_path)
        return f'Validation error: {self.message}\nPath: error_path_str'


class Field:
    """Common Base class for simple field types (int, string, bool and so on), not to be instantiated directly.  Must be derived from.  Instantiations of this class are meant to be stored as static variables of a Map or Document."""
    def __init__(self, *, firestore_type, schema_name, allow_missing,
                 allow_null, parse_missing_as_None):
        if type(self) == Field:
            raise typeerror(
                'Cannot construct Field object directly, must use a subclass of Field.'
            )
        self._firestore_type = firestore_type
        self._schema_name = schema_name
        self._allow_missing = allow_missing
        self._allow_null = allow_null
        self._parse_missing_as_None = parse_missing_as_None
        self.containing_cls = None

    def _init_fields(self, schema_name, containing_cls):
        """Invoked by the containing class.  Provides context e.g. if a different schema name is preferred and allows this field to store a reference to the containing class."""
        self._schema_name = schema_name
        self.containing_cls = containing_cls

    def _validate_dict(self, val):
        """Type check a val, after reading from or before writing to the firestore.  None is allowed if self._allow_null is set to True."""
        if val is None:
            if self._allow_null:
                return
            else:
                raise ValidatorException(
                    f'field {self._schema_name} may not be null')
        if not isinstance(val, self._firestore_type):
            raise ValidatorException(
                f'expected instance of type {self._firestore_type.__name__} but got {type(val).__name__}.\nValue {val}'
            )

    @staticmethod
    def dict_to_python(cls, val):
        return val
    @staticmethod
    def python_to_dict(cls, val):
        return val
    def __lt__(self, val):
        raise NotImplementedError()


class Number(Field):
    def __init__(self, *, rename=None, allow_missing=False, allow_null=False, parse_missing_as_None=False):
        super().__init__(firestore_type=numbers.Number,
                         schema_name=rename,
                         allow_missing=allow_missing,
                         allow_null=allow_null, parse_missing_as_None=parse_missing_as_None)


class String(Field):
    def __init__(self, *, rename=None, allow_missing=False, allow_null=False, parse_missing_as_None=False):
        super().__init__(firestore_type=str,
                         schema_name=rename,
                         allow_missing=allow_missing,
                         allow_null=allow_null,parse_missing_as_None=parse_missing_as_None)


class Boolean(Field):
    def __init__(self, *, rename=None, allow_missing=False, allow_null=False):
        super().__init__(firestore_type=bool,
                         schema_name=rename,
                         allow_missing=allow_missing,
                         allow_null=allow_null, parse_missing_as_None=parse_missing_as_None)

class FirestoreFields:
    pass


class Map(Field):
    def __init__(self, *, rename=None, allow_missing=False, allow_null=False, parse_missing_as_None=False):
        super().__init__(firestore_type=dict,
                         schema_name=rename,
                         allow_missing=allow_missing,
                         allow_null=allow_null, parse_missing_as_None=parse_missing_as_None)
    def _get_fields(cls):
        return ((name, field._schema_name, field)
                for (name, field) in vars(cls).items()
                if isinstance(field, Field))

    def _init_fields(self, schema_name, containing_cls):
        super()._init_fields(schema_name, containing_cls)
        cls = type(self)
        cls._firestore_fields = FirestoreFields()
        to_delete = set()
        for (name, schema_name, field) in Map._get_fields(cls):
            field._init_fields(schema_name or name, self)
            setattr(cls._firestore_fields, name, field)
            to_delete.add(name)
        for name in to_delete:
            delattr(cls, name)

    def _validate_dict(self, val):
        super()._validate_dict(val)
        if val is None:
            return None
        #now check members
        for (name, schema_name, field) in Map._get_fields(type(self)._firestore_fields):
            if schema_name not in val:
                if field._allow_missing:
                    continue
                else:
                    raise ValidatorException(
                        f'field "{schema_name}" is missing.')
            field._validate_dict(val[schema_name])
    @staticmethod
    def dict_to_python(cls, val):
        if val is None:
            return None
        obj = cls()
        for (name, schema_name, field) in Map._get_fields(cls._firestore_fields):
            if schema_name in val:
                setattr(obj, name, field.dict_to_python(type(field), val[schema_name]))
            elif field._allow_missing and field._parse_missing_as_None:
                setattr(obj, name, None)
        return obj

    @staticmethod
    def python_to_dict(cls, val):
        if val is None:
            return None
        obj = dict()
        for (name, schema_name, field) in Map._get_fields(cls._firestore_fields):
            if hasattr(val,name):
                obj[schema_name] = field.python_to_dict(type(field), getattr(val, name))
        return obj
