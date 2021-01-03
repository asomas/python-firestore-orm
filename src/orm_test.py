import os
import google.auth.credentials
from unittest import mock
from firebase_admin import firestore, auth

cred = mock.Mock(spec=google.auth.credentials.Credentials)
db = firestore.Client(project=os.environ.get("FIRESTORE_PROJECT_ID"),
                      credentials=cred)

# add single
col_ref = db.collection('workers')
col_ref.add({"first_name": "Jane", "last_name": "Doe"})

# add batch
batch = db.batch()
for i in range(10):
    doc_ref = col_ref.document()
    batch.set(doc_ref, {
        "first_name": f"worker{i+1}",
        "last_name": f"worker{i+1}"
    })
batch.commit()

# retrieve
workers = col_ref.get()
print(len(workers))
assert len(workers) == 11
for w in workers:
    print(w.to_dict())
