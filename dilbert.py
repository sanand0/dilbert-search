import wsgiref.handlers, datetime, random

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.ext.webapp import template

user     = users.get_current_user()
oneday   = datetime.timedelta(1)
startday = datetime.date(1993, 01, 01).toordinal()
endyear  = '2008'
today    = datetime.date.today().toordinal()
now      = datetime.datetime.now()

class Dilbert(db.Model):
    date = db.StringProperty     (required=True)
    desc = db.TextProperty       (required=True)
    user = db.UserProperty       (required=True)
    time = db.DateTimeProperty   (required=True, auto_now_add=True)

class User(db.Model):
    user = db.UserProperty       (required=True)
    num  = db.IntegerProperty    (required=True)
    time = db.DateTimeProperty   (required=True, auto_now_add=True)

class DilbertPage(webapp.RequestHandler):
    def get(self, date = None):
        if date:
            q = Dilbert.all().filter('date = ', date).order('-time').fetch(5)
            out = { 'date': date, 'next': self.next(date), 'prev': self.prev(date) }
            out['desc']     = q and q[0].desc or ''
            out['past']     = len(out['desc']) > 1 and q[1:] or None
            out['user']     = user
            out['users']    = User.all().order('-num').fetch(10)
            out['unused']   = self.unused()
            out['img_date'] = out['date'] > endyear and 'http://www.geek.nl/pics/dilbert-arch/dilbert-' + out['date'] + '.gif' or '/' + out['date'][:7] + '/' + out['date'] + '.gif'
            out['img_next'] = out['next'] > endyear and 'http://www.geek.nl/pics/dilbert-arch/dilbert-' + out['next'] + '.gif' or '/' + out['next'][:7] + '/' + out['next'] + '.gif'
            out['img_prev'] = out['prev'] > endyear and 'http://www.geek.nl/pics/dilbert-arch/dilbert-' + out['prev'] + '.gif' or '/' + out['prev'][:7] + '/' + out['prev'] + '.gif'
            self.response.out.write(template.render('dilbert.html', out))
        else:
            self.redirect('/dilbert/' + self.unused(), True)

    # Request to add a description for a date
    def post(self, date):
        desc = self.request.get('desc')
        if user and desc:
            q = Dilbert.all().filter('date = ', date).order('-time').fetch(1)
            # Add the description if it is different from the previous entry
            if q and q[0].desc != desc or not q: Dilbert(date=date, desc=desc, user=user).put()

            # Update the user stats
            q = User.all().filter('user = ', user).fetch(1)
            if q:
                q[0].num = q[0].num + 1
                q[0].time = now
                q[0].put()
            else:
                 User(user=user, num=1).put()

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
        ('/',                   DilbertPage),
        ('/dilbert/(\d*)',      DilbertPage),
        ('/dilbert/export',     ExportPage),
        ('/logout',             LogoutPage),
        ('/logout/(.+)',        LogoutPage),
        ('/login',              LoginPage),
        ('/login/(.+)',         LoginPage),
    ],
    debug=True)
wsgiref.handlers.CGIHandler().run(application)
