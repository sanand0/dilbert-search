'''
- Start with an unfilled comic strip

'''

import wsgiref.handlers
import datetime
import random

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.webapp import template

user     = users.get_current_user()
oneday   = datetime.timedelta(1)
startday = datetime.date(2001, 01, 01).toordinal()
today    = datetime.date.today().toordinal()

class Dilbert(db.Model):
    date = db.StringProperty     (required=True)
    desc = db.TextProperty       (required=True)
    user = db.UserProperty       (required=True)
    time = db.DateTimeProperty   (required=True, auto_now_add=True)

class DilbertPage(webapp.RequestHandler):
    def get(self, date = None):
        if date:
            q = Dilbert.all().filter('date = ', date).order('-time').fetch(5)
            desc = q and q[0].desc or ''
            past = len(desc) > 1 and q[1:] or None
            self.response.out.write(template.render('dilbert.html', { 'date': date, 'desc': desc, 'past': past, 'user': user, 'next': self.next(date), 'prev': self.prev(date), 'unused': self.unused() }))
        else:
            self.redirect('/dilbert/' + self.unused(), True)

    # Request to add a description for a date
    def post(self, date):
        if user:
            q = Dilbert.all().filter('date = ', date).order('-time').fetch(1)
            desc = self.request.get('desc')
            # Add the description if it is different from the previous entry
            if q and q[0].desc != desc or not q: Dilbert(date=date, desc=desc, user=user).put()
            self.redirect('/dilbert/' + self.next(date))
        else:
            self.redirect('/login/' + date)

    def next(self, date):
        d = datetime.date(int(date[:4]), int(date[4:6]), int(date[6:8])) + oneday
        return d.isoformat().replace("-", "")

    def prev(self, date):
        d = datetime.date(int(date[:4]), int(date[4:6]), int(date[6:8])) - oneday
        return d.isoformat().replace("-", "")

    def rand(self):
        return datetime.date.fromordinal( random.randrange(startday, today) ).isoformat().replace("-", "")

    def unused(self):
        date = self.rand()
        while Dilbert.all().filter('date = ', date).get():
            date = self.rand()
        return date

class ExportPage(webapp.RequestHandler):
    def get(self):
        if user:
            q = Dilbert.all().order('-time')
            self.response.headers["Content-Type"] = "application/javascript"
            self.response.out.write('dilbert([\n')
            done = {}
            for item in q:
                if done.get(item.date, None): continue
                else: done[item.date] = 1
                self.response.out.write('["' + item.date + '","' + item.desc.replace('\n', '\\n').replace('\r', '').replace('"', '\\"') + '"],\n')
            self.response.out.write('0])')
        else:
            self.redirect('/login/export')

class LogoutPage(webapp.RequestHandler):
    def get(self, date = None):
        if date: self.redirect(users.create_logout_url('/dilbert/' + date))
        else:    self.redirect(users.create_logout_url('/dilbert'))

class LoginPage(webapp.RequestHandler):
    def get(self, date = None):
        if date: self.redirect(users.create_login_url('/dilbert/' + date))
        else:    self.redirect(users.create_login_url('/dilbert'))

application = webapp.WSGIApplication([
        ('/',               DilbertPage),
        ('/dilbert/(\d*)',  DilbertPage),
        ('/dilbert/export', ExportPage),
        ('/logout',         LogoutPage),
        ('/logout/(.+)',    LogoutPage),
        ('/login',          LoginPage),
        ('/login/(.+)',     LoginPage),
    ],
    debug=True)
wsgiref.handlers.CGIHandler().run(application)
