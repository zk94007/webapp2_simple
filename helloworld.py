import cgi
import datetime
import urllib
import wsgiref.handlers
import os

from google.appengine.ext.webapp import template
from google.appengine.ext import ndb
from google.appengine.api import users
import webapp2
from webapp2_extras import jinja2

class Greeting(ndb.Model):
    """Models an individual Guestbook entry with an author, content, and date."""
    author = ndb.UserProperty()
    content = ndb.StringProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)

    @classmethod
    def query_book(cls, ancestor_key):
        return cls.query(ancestor=ancestor_key).order(-cls.date)

class BaseHandler(webapp2.RequestHandler):

    @webapp2.cached_property
    def jinja2(self):
        # Returns a Jinja2 renderer cached in the app registry.
        return jinja2.get_jinja2(app=self.app)

    def render_response(self, _template, **context):
        # Renders a template and writes the result to the response.
        rv = self.jinja2.render_template(_template, **context)
        self.response.write(rv)

class MainPage(BaseHandler):
    def get(self):
        guestbook_name=self.request.get('guestbook_name')
        ancestor_key = ndb.Key("Guestbook", guestbook_name or "default_guestbook")
        greetings = Greeting.query_book(ancestor_key).fetch(20)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'


        template_values = {
            'greetings': greetings,
            'url': url,
            'url_linktext': url_linktext,
        }        
        self.render_response('index.html', **template_values)

        # path = os.path.join(os.path.dirname(__file__), 'index.html')
        # self.response.out.write(template.render(path, template_values))

class Guestbook(webapp2.RequestHandler):
  def post(self):
    # We set the same parent key on the 'Greeting' to ensure each greeting is in
    # the same entity group. Queries across the single entity group will be
    # consistent. However, the write rate to a single entity group should
    # be limited to ~1/second.
    guestbook_name = self.request.get('guestbook_name')
    ancestor_key = ndb.Key("Guestbook", guestbook_name or "default_guestbook")
    greeting = Greeting(parent=ancestor_key)

    if users.get_current_user():
      greeting.author = users.get_current_user()

    greeting.content = self.request.get('content')
    greeting.put()
    self.redirect('/?' + urllib.urlencode({'guestbook_name': guestbook_name}))


app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/sign', Guestbook)
], debug=True)