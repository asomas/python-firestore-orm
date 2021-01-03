import os
import google.auth.credentials
from unittest import mock
from firebase_admin import firestore, auth

from firestore_orm import *
from fields import *

cred = mock.Mock(spec=google.auth.credentials.Credentials)

init_orm(project=os.environ.get('FIRESTORE_PROJECT_ID'), credentials=cred)

#currently supported field types, Number, String, Boolean, DocRef and Map.
#coming soon is list, DateTime, Coordinate and more.

#Every field can be parameterised as follows:
#allow_missing, defaults to False, if True, do not throw a ValidationException if a document fetched does not have the specified field.
#allow_null, defaults to False, if True, do not throw a validationException if a document fetched has the specified field set to null/None.
#rename, set the name of the field in the map or document, if unspecified, the name is taken from the python property name as below.


#defining a map field to be part of a containing document
class Address(Map):
    house_name = String(allow_missing=True)
    #field with name house_name that can be missing
    postcode = String(rename='zip_code')

    #field that cannot be null or missing and in the firestore is saved as zip_code
    def __str__(self):
        return f'address(house_name={self.house_name}, postcode={self.postcode})'


#define a document, must use collection annotation, collection annotation has optional argument name.  If not specified, collection name is the class name.
@collection()
class Person(Document):
    name = String()
    age = Number()
    address = Address(allow_null=True)

    def __str__(self):
        return f'Person(name={self.name}, age={self.age}, address={self.address})'


p = Person()
p.name = 'fudge'
p.age = 5
a = Address()
a.postcode = 'abcde'
p.address = a

print(f'storing {p}')
p.store()
#id is now in p.doc_ref

q = p.doc_ref.get()
print(f'received {q}')

#change ID
q.doc_ref = DocRef(Person, id='my_special_id')
q.name = 'foo2'
q.address = None

print(f'storing {q}')

q.store()

#fetch q using specified ID
r = DocRef(Person, id='my_special_id').get()
print(f'received {r}')
