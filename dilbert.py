import wsgiref.handlers, datetime, random

from google.appengine.ext import webapp
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from time import strftime

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

class Dump(db.Model):
    year = db.StringProperty     (required=True)
    desc = db.TextProperty       (required=True)

def url(date): return date > endyear and 'http://www.geek.nl/pics/dilbert-arch/dilbert-' + date + '.gif' or 'http://dilbert-search.appspot.com/' + date[:7] + '/' + date + '.gif'

class DilbertPage(webapp.RequestHandler):
    def get(self, date = None):
        if date:
            q = Dilbert.all().filter('date = ', date).order('-time').fetch(5)
            out = { 'date': date, 'next': self.next(date), 'prev': self.prev(date) }
            out['ie']       = self.request.headers['User-Agent'].find('MSIE') >= 0 and 1 or 0
            out['desc']     = q and q[0].desc or ''
            out['author']   = q and q[0].user or ''
            out['past']     = len(out['desc']) > 1 and q[1:] or None
            out['user']     = user
            out['users']    = User.all().order('-num').fetch(10)
            out['unused']   = self.unused()
            out['few_words'] = self.request.get('few_words')
            out['thanks']   = self.request.get('thanks')
            out['img_date'] = url(out['date'])
            out['img_next'] = url(out['next'])
            out['img_prev'] = url(out['prev'])
            self.response.out.write(template.render('dilbert.html', out))
        else:
            self.redirect('/dilbert/' + self.unused(), True)

    # Request to add a description for a date
    def post(self, date):
        desc = self.request.get('desc')
        if user and desc:
            wc = len(desc.split())
            if wc < 8:
                self.redirect('/dilbert/' + date + '?few_words=' + str(wc))
            else:
                q = Dilbert.all().filter('date = ', date).order('-time').fetch(1)
                # Add the description if it is different from the previous entry
                if q and q[0].desc != desc or not q: Dilbert(date=date, desc=desc, user=user).put()

                # Update the user stats
                q = User.all().filter('user = ', user).fetch(1)
                if q:
                    q[0].num += 1
                    q[0].time = now
                    q[0].put()
                else:
                     User(user=user, num=1).put()

                # self.redirect('/dilbert/' + self.next(date) + '?thanks=1')
                self.redirect('/dilbert/' + self.unused() + '?thanks=1', True)
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
        self.response.headers["Content-Type"] = "text/plain"
        self.response.out.write('id\tquote\n' + '\n'.join((item.desc for item in Dump.all().order('year'))))

class FeedPage(webapp.RequestHandler):
    def get(self):
        self.response.headers["Content-Type"] = "text/xml"
        entries = Dilbert.all().order('-time').fetch(100)
        for entry in entries: entry.url = url(entry.date)
        self.response.out.write(template.render('feed.xml', {'entries': entries, 'updated': entries[0].time}))

class DumpPage(webapp.RequestHandler):
    def get(self, year):
        if users.is_current_user_admin():
            done, dump = {}, []
            for item in Dilbert.all().order('date').filter('date >= ', year + '0101').filter('date <= ', year + '1231').order('-time'):
                if not done.has_key(item.date):
                    done[item.date] = 1
                    dump.append(item.date + '\t' + item.desc.replace('\n', ' ').replace('\r', ''))
            if dump:
                entity = Dump.all().filter('year = ', year).get() or Dump(year=year, desc='desc')
                entity.desc = '\n'.join(dump)
                entity.put()
            self.response.out.write('Dumped year: ' + year)
        else:
            self.response.out.write('Only the administrator can dump data, because it uses a lot of CPU. This is done daily.')

class LogoutPage(webapp.RequestHandler):
    def get(self, date = None):
        if date: self.redirect(users.create_logout_url('/dilbert/' + date))
        else:    self.redirect(users.create_logout_url('/dilbert'))

class LoginPage(webapp.RequestHandler):
    def get(self, date = None):
        if date: self.redirect(users.create_login_url('/dilbert/' + date))
        else:    self.redirect(users.create_login_url('/dilbert'))

application = webapp.WSGIApplication([
        ('/',                           DilbertPage),
        ('/dilbert/(\d*)',              DilbertPage),
        ('/dilbert/export',             ExportPage),
        ('/dilbert/export/(\d\d\d\d)',  DumpPage),
        ('/dilbert/rss',                FeedPage),
        ('/logout',                     LogoutPage),
        ('/logout/(.+)',                LogoutPage),
        ('/login',                      LoginPage),
        ('/login/(.+)',                 LoginPage),
    ],
    debug=True)
wsgiref.handlers.CGIHandler().run(application)
