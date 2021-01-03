from firestore_orm import *
import fields

class Job(fields.Map):
    volunteer = fields.Boolean()
    title = fields.String()

@collection()
class Worker(Document):
    name = fields.String()
    job = Job()


w = Worker()
w.job = Job()
w.name = "foo"
w.job.volunteer = False
w.job.title = "fudge"
w.validate()