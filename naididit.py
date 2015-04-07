import os

import jinja2
import webapp2

from google.appengine.ext import db


template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)


class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self,template, **params):
		t= jinja_env.get_template(template)
		return t.render(params)

	def render(self,template,**kw):
		self.write(self.render_str(template,**kw))

class Blog(db.Model):
	title=db.StringProperty(required = True)
	content =db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)		

class MainPage(Handler):

	def render_naididit(self,blgtitle="",blgcontent="",error=""):
		blog = db.GqlQuery("SELECT * FROM Blog ORDER BY created DESC")

		self.render("naididit.html",blgtitle=blgtitle,blgcontent=blgcontent,error=error,blog=blog)

	def get(self):	 
		self.render_naididit()
		#self.response.headers['Content-Type'] = 'text/plain'
		#self.render("naididit.html")
			

	def post(self):
		title=self.request.get("blgtitle")
		content= self.request.get("blgcontent")
		#di=makeindex(title,content)

		#self.render_naididit(content,title)
		#self.response.headers['Content-Type'] = 'text/plain'
		#self.write(self.request)

		if title and content:

			a = Blog(title = title,content = content)
			a.put()

			self.redirect('/')
			
		else:
			error = "Got some rendering error"
			self.render_naididit(content,title,error)

app=webapp2.WSGIApplication([('/',MainPage),],debug = True)				