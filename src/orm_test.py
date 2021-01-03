import os
import google.auth.credentials
from unittest import mock
from firebase_admin import firestore, auth

from firestore_orm import *
from fields import *

cred = mock.Mock(spec=google.auth.credentials.Credentials)

init_orm(project=os.environ.get('FIRESTORE_PROJECT_ID'), credentials=cred)


class Address(Map):
    house_name = String(allow_missing=True)
    postcode = String()
    def __str__(self):
        return f'address(house_name={self.house_name}, postcode={self.postcode})'

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


q = p.doc_ref.get()
print(f'received {q}')

q.doc_ref = DocRef(Person, id='my_special_id')
q.name = 'foo2'
q.address = None

print(f'storing {q}')

q.store()
r = DocRef(Person, id='my_special_id').get()
print(f'received {r}')
