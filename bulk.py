import datetime
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.tools import bulkloader

class Dilbert(db.Model):
    date = db.StringProperty     (required=True)
    desc = db.TextProperty       (required=True)
    user = db.UserProperty       (required=True)
    time = db.DateTimeProperty   (required=True, auto_now_add=True)

class DilbertLoader(bulkloader.Loader):
    def __init__(self):
        bulkloader.Loader.__init__(self, 'Dilbert',
            [('date', str),
             ('desc', lambda x: x.replace('\\n', '\n')),
             ('user', lambda x: users.User(x))
            ])

loaders = [DilbertLoader]
