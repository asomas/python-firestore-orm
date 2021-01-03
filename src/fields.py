import numbers

SPECIAL_KEYS = {'_schema_name', '_allow_missing', '_allow_null'}


class ValidatorException(Exception):
    def __init__(self, message):
        self.message = message
        self.error_path = []

    def str(self):
        error_path_str = ''.join(
            f'["{segment}"]' if type(segment) == str else f'[{segment}]'
            for segment in self.error_path)
        return f'Validation error: {self.message}\nPath: error_path_str'


class Field(property):
    def __init__(self, *, firestore_type, schema_name, allow_missing,
                 allow_null):
        if type(self) == Field:
            raise typeerror(
                'Cannot construct Field object directly, must use a subclass of Field.'
            )
        super().__init__(
            lambda containing_cls: self._get_value(containing_cls),
            lambda containing_cls, val: self._set_value(containing_cls, val),
            lambda containing_cls: self._del_value(containing_cls),
            f'A property of type {firestore_type.__name__} with name {schema_name}'
        )
        self._firestore_type = firestore_type
        self._schema_name = schema_name
        self._allow_missing = allow_missing
        self._allow_null = allow_null

    def _type_check(self, val):
        if val is None:
            if self._allow_null:
                return
            else:
                raise ValidatorException(
                    f'field {self._schema_name} may not be null')
        if not isinstance(val, self._firestore_type):
            raise ValidatorException(
                f'expected instance of type {self._firestore_type.__name__} but got {type(val).__name__}'
            )

    def _init_fields(self, schema_name, containing_cls):
        self._schema_name = schema_name
        self.containing_cls = containing_cls

    def _validate(self, parent):
        def contains_key(key, obj):
            if type(obj) == list:
                return key >= 0 and key < len(obj)
            elif type(obj) == dict:
                return key in obj
            else:
                raise typeerror(obj)

        if self._schema_name is None:
            return None
        if not contains_key(self._schema_name, parent._firestore_data):
            if self._allow_missing:
                return None
            else:
                raise ValidatorException(
                    f'field "{self._schema_name}" is missing.')
        val = parent._firestore_data[self._schema_name]
        self._type_check(val)
        return val

    def _get_value(self, containing_cls):
        return containing_cls._firestore_data.get(self._schema_name)

    def _set_value(self, containing_cls, val):
        self._type_check(val)
        containing_cls._firestore_data[self._schema_name] = val

    def _del_value(self, containing_cls):
        raise NotImplementedError()

    def __lt__(self, val):
        raise NotImplementedError()


class Number(Field):
    def __init__(self, *, rename=None, allow_missing=False, allow_null=False):
        super().__init__(firestore_type=numbers.Number,
                         schema_name=rename,
                         allow_missing=allow_missing,
                         allow_null=allow_null)


class String(Field):
    def __init__(self, *, rename=None, allow_missing=False, allow_null=False):
        super().__init__(firestore_type=str,
                         schema_name=rename,
                         allow_missing=allow_missing,
                         allow_null=allow_null)


class Boolean(Field):
    def __init__(self, *, rename=None, allow_missing=False, allow_null=False):
        super().__init__(firestore_type=bool,
                         schema_name=rename,
                         allow_missing=allow_missing,
                         allow_null=allow_null)


class Map(Field):
    def __init__(self, *, rename=None, allow_missing=False, allow_null=False):
        super().__init__(firestore_type=dict,
                         schema_name=rename,
                         allow_missing=allow_missing,
                         allow_null=allow_null)
        self._firestore_data = {}

    def _get_fields_cls(cls):
        return ((name, field._schema_name, field)
                for (name, field) in vars(cls).items()
                if isinstance(field, Field))

    def _get_fields(self):
        return Map._get_fields_cls(type(self))

    def _init_fields(self, schema_name, containing_cls):
        super()._init_fields(schema_name, containing_cls)
        for (name, schema_name, field) in self._get_fields():
            field._init_fields(schema_name or name, self)

    def _validate(self, parent):
        val = super()._validate(parent)
        if val is None:
            return None
        #now check members
        self._firestore_data = parent._firestore_data[self._schema_name]
        for (name, schema_name, field) in self._get_fields():
            field._validate(self)

    def _get_value(self, containing_cls):
        return self if containing_cls._firestore_data[
            self._schema_name] is not None else None

    def _set_value(self, containing_cls, val):
        if val is None:
            if self._allow_null:
                containing_cls._firestore_data[self._schema_name] = None
                self._firestore_data = {}
                return
            else:
                raise ValidatorException(
                    f'field {self._schema_name} may not be null')

        if type(self) != type(val):
            raise ValidatorException(
                f'expected instance of type {type(self).__name__} but got {type(val).__name__}'
            )
        self.__dict__.update(
            {k: v
             for (k, v) in val.__dict__.items() if k not in SPECIAL_KEYS})
        containing_cls._firestore_data[
            self._schema_name] = self._firestore_data
