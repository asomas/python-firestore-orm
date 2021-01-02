import numbers
SPECIAL_KEYS = {'_schema_name','_allow_missing','_allow_null'}

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
        super().__init__(
            lambda self_parent: self._get_value(self_parent),
            lambda self_parent, val: self._set_value(self_parent, val),
            lambda self_parent: self._del_value(self_parent),
            f'A property of type {firestore_type.__name__} with name {schema_name}'
        )
        self._firestore_type = firestore_type
        self._schema_name = schema_name
        self.allow_missing = allow_missing
        self.allow_null = allow_null

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
            if self.allow_missing:
                return None
            else:
                raise ValidatorException(f'field {self._schema_name} is missing.')
        val = parent._firestore_data[self._schema_name]
        self._type_check(val)
        return val

    def _get_value(self, self_parent):
        return self_parent._firestore_data[self._schema_name]

    def _set_value(self, self_parent, val):
        self._type_check(val)
        self_parent._firestore_data[self._schema_name] = val

    def _del_value(self, self_parent):
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
        super().__init__(firestore_type=dict, schema_name=rename, 
                         allow_missing=allow_missing,
                         allow_null=allow_null)
        self._firestore_data = {}
        for (name,schema_name,field) in self._get_fields():
            field._schema_name = schema_name or name

    def _get_fields(self):
        return ((name, field._schema_name,field) for (name, field) in vars(type(self)).items()
                if isinstance(field, Field))

    def _validate(self, parent):
        val = super()._validate(parent)
        if val is None:
            return None
        #now check members
        self._firestore_data = parent._firestore_data[self._schema_name]
        for (name,schema_name,field) in self._get_fields():
            field._validate(self)

    def _get_value(self, self_parent):
        return self

    def _set_value(self, self_parent, val):
        if type(self) != type(val):
            raise ValidatorException(
                f'expected instance of type {type(self).__name__} but got {type(val).__name__}'
            )
        self.__dict__.update({k:v for (k,v) in val.__dict__.items() if k not in SPECIAL_KEYS})
        self_parent._firestore_data[self._schema_name] = self._firestore_data
        


class Document(Map):
    def __init__(self, *, rename='default', allow_missing=False, allow_null=False):
        super().__init__(rename=rename,
                         allow_missing=allow_missing,
                         allow_null=allow_null)


    
    def validate(self):
        class Temp:
            _firestore_data = {'default':self._firestore_data}
        self._validate(Temp)


