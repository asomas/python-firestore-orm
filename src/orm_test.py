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
    house_name = String(allow_missing=True, parse_missing_as_None=True)
    #field with name house_name that can be missing, and when missing, parse it into python None.
    #since allow_null is false , the None will need to be deleted (missing) or set to a non null value.
    postcode = String(rename='zip_code')
    #field that cannot be null or missing and in the firestore is saved as zip_code

    def __str__(self):
        return f'address(postcode={self.postcode}, house_name={getattr(self, "house_name", None)})'



#Define a Document.
#Document classes must be annotated with @collection().
#The name of the collection as stored in the firestore is taken from the class name, an optional parameter name `@collection(name=...)` can be used to choose a different name.
@collection()
class Person(Document):
    name = String()
    age = Number()
    address = Address(allow_null=True)

    def __str__(self):
        return f'Person(name={self.name}, age={self.age}, address={self.address})'

#set manually or from json like dict
p = Person()
p.name = 'fudge'
p.age = 5
a = Address()
a.postcode = 'abcde'
p.address = a

#from dict
q = Document.from_dict(Person, {'name': 'fudge2', 'age': 10, 'address': None})

#Save the document to the firestore with a specific ID.
print(f'storing {p}')
p.store('hello')

#Save a document to the firestore with a firestore chosen ID.
print(f'storing {q}')
q.store()

#Get the ID from q.doc_ref.
doc_ref = q.doc_ref

#if doc_ref cannot be used, use the `key_name` parameter to the collection, `@collection(key_name=...)` to change the name of the python class member in wich the ID is stored.

p_1 = Document.get(Person, 'hello')
print(f'received {p_1}')

#get the other person object from the doc_ref.  Either,
q_1 = doc_ref.get()
#or
q_2 = Document.get(Person, doc_ref)

print(f'fetched q_1 as {q_1}')
print(f'fetched q_2 as {q_2}')
#resave with different values but same ID
q_1.name = 'foo2'
q_1.address = None
print(f'storing {q_1}')
q_1.store()

