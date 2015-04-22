import os
import re
from string import letters

import jinja2
import webapp2

from google.appengine.ext import db


template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)

def render_str(template, **params):
		t= jinja_env.get_template(template)
		return t.render(params)

def render(self,template,**kw):
		self.write(self.render_str(template,**kw))

				

class BlogHandler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self,template, **params):
		t= jinja_env.get_template(template)
		return t.render(params)

	def render(self,template,**kw):
		self.write(self.render_str(template,**kw))

#defines the datastore`s parent for organizations sake
def blog_key(name = 'default'):
	return db.Key.from_path('blogs',name)		

class Blog(db.Model):
	subject=db.StringProperty(required = True)
	content =db.TextProperty(required = True)
	created = db.DateTimeProperty(auto_now_add = True)
	#sets property of when last modified	
	last_modified = db.DateTimeProperty(auto_now = True)

	#renders in html new line(stops html from merging white spaces)
	def render(self):
		self._render_text = self.content.replace('\n','<br>')
		return render_str("post.html", p = self)



class BlogFront(BlogHandler):
	def get(self):
		blog = db.GqlQuery("SELECT * FROM Blog ORDER BY created DESC limit 10")
		self.render('front.html',blog = blog)
		#same as 
		#blog = Blog.all().order('-created')
		#self.render('front.html',blog = blog)

class BlogPost(BlogHandler):
	def get(self,blog_id):
		key = db.Key.from_path('Blog',int(blog_id),parent=blog_key())
		blog=db.get(key)
		if not blog:
			self.error(404)
		return self.render('permalink.html',blog=blog)
		
class NewPost(BlogHandler):
	def get(self):
		self.render("newpost.html")

	def post(self):
		subject=self.request.get('subject')
		content= self.request.get('content')

		if subject and content:
			p=Blog(parent=blog_key(),subject=subject,content=content)
			p.put()
			x=str(p.key().id())
			#self.write('/blog / %s' % x)
			#self.redirect('/blog / %s' % x )
			self.redirect("/blog/%s"%x)
			#self.redirect(r'/blog/(\d+)>',PostHandler)
		else:
			error = "subject and content,please !"
			self.render("newpost.html",subject=subject,content=content,error=error)		


class PostHandler(BlogHandler):
	def get(self,blog_id):
		p=Blog.get_by_id(blog_id)
		if p:
			self.render('permalink.html',p=p)
		
		



class MainPage(BlogHandler):

#	def render_naididit(self,blgtitle="",blgcontent="",error=""):
#		blog = db.GqlQuery("SELECT * FROM Blog ORDER BY created DESC")
#
#		self.render("naididit.html",blgtitle=blgtitle,blgcontent=blgcontent,error=error,blog=blog)
##
	def get(self):	
		#self.write("front welcome page") 
#		self.render_naididit()
		#self.response.headers['Content-Type'] = 'text/plain'
		self.render("newpost.html")

	def post(self):
		NewPost(BlogHandler)

#		subject=self.request.get('subject')
#		content= self.request.get('content')

#		if subject and content:
#			p=Blog(parent=blog_key(),subject=subject,content=content)
#			p.put()
#			self.redirect('/blog/%s' % str(p.key().id()))
#		else:
#			error = "subject and content,please !"
#			self.render("newpost.html",subject=subject,content=content,error=error)		

	
			

#	def post(self):
#		title=self.request.get("blgtitle")
#		content= self.request.get("blgcontent")
		#di=makeindex(title,content)

		#self.render_naididit(content,title)
		#self.response.headers['Content-Type'] = 'text/plain'
		#self.write(self.request)

#		if title and content:

#			a = Blog(title = title,content = content)
#			a.put()

#			self.redirect('/h')
			
#		else:
#			error = "Got some rendering error"
#			self.render_naididit(content,title,error)

app=webapp2.WSGIApplication([('/',MainPage),
							  ('/blog/?',BlogFront),
							  ('/blog/([0-9]+)',BlogPost),
							  ('/blog/[0-9]+)',PostHandler),
							  ('/blog/newpost',NewPost),
							  ],
							  debug = True)				