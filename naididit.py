import os
import re
import random
import hashlib
import hmac
from string import letters

import jinja2
import webapp2

from google.appengine.ext import db


template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
								autoescape = True)

secret = 'P@cs=iz8o?Wz~;QJ3?gE.h,|mbm,!%.'

def render_str(template, **params):
		t= jinja_env.get_template(template)
		return t.render(params)

def make_secure_val(val):
	return '%s|%s' % (val, hmac.new(secret,val).hexdigest())	

def check_secure_val(secure_val):
	val = secure_val.split('|')[0]
	if secure_val == make_secure_val(val):
		return val 		

#def render(self,template,**kw):
		#self.write(self.render_str(template,**kw))

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
	return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")	
def valid_password(password):	
	return password and PASS_RE.match(password)

EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
	return not email or EMAIL_RE.match(email)


class BlogHandler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self,template, **params):
		t= jinja_env.get_template(template)
		return t.render(params)

	def render(self,template,**kw):
		self.write(self.render_str(template,**kw))

	def set_secure_cookie(self,name,val):
		cookie_val = make_secure_val(val)
		self.response.headers.add_header(
			'Set-Cookie',
			'%s=%s; Path=/' % (name, cookie_val))

	def read_secure_cookie(self,name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and check_secure_val(cookie_val)

	def login(self,user):
		self.set_secure_cookie('user_id',str(user.key().id()))	

	def logout(self):
		self.response.headers.add_header('Set-Cookie','user_id=; Path=/')

	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		uid = self.read_secure_cookie('user_id')
		self.user = uid and User.by_id(int(uid))			
			

#user stuff

def make_salt(length = 5):
	return ''.join(random.choice(letters) for x in xrange(length))

def make_pw_hash(name, pw, salt = None):
	if not salt:
		salt = make_salt()
	h = hashlib.sha256(name + pw + salt).hexdigest()
	return '%s,%s' % (salt, h)

def valid_pw(name, password, h):
	salt = h.split(',')[0]
	return h == make_pw_hash(name, password, salt)

def users_key(group = 'default'):
	return db.Key.from_path('users',group)

class User(db.Model):
	name=db.StringProperty(required = True)
	pw_hash = db.StringProperty(required = True)
	email = db.StringProperty()

	@classmethod
	def by_id(cls, uid):
		return User.get_by_id(uid, parent = users_key())

	@classmethod
	def by_name(cls, name):
		u = User.all().filter('name =', name).get()
		return u

	@classmethod
	def register(cls, name, pw, email = None):
		pw_hash = make_pw_hash(name, pw)
		return User(parent = users_key(),
					name = name,
					pw_hash = pw_hash,
					email = email)
	@classmethod
	def login(cls, name, pw):
		u = cls.by_name(name)
		if u and valid_pw(name, pw, u.pw_hash):
			return u

	


#Blog stuff





class Signup(BlogHandler):
	def get(self):
		self.render("userregistration.html")	

	def post(self): 
		have_error = False
		self.username = 	self.request.get('username')
		self.password = self.request.get('password')
		self.verify = self.request.get('verify')
		self.email = self.request.get('email')

		params = dict(username = self.username, email= self.email)


		if not valid_username(self.username):
			params['error_username']= "That`s not a valid user`s  name."
			have_error=True

		if not	valid_password(self.password):
			params['error_password'] = "That`s not a valid password."
			have_error = True
		elif self.password != self.verify:
			params['error_verify'] = "Your password didn`t match."
			have_error = True	

		if not valid_email(self.email):
			params['error_mail'] = "That`s not a valid email."
			have_error = True

		if have_error:
			self.render('userregistration.html', **params)
		else:
			#self.redirect('/welcome?username='+username)
			self.done()

	def done(self, *a, **kw):
		raise NotImplementedError		

class Welcome(Signup):
	def done(self):
		self.redirect('/welcome?username='+username)






class Register(Signup):
	def done(self):
		#make sure the user does not exist
		u = User.by_name(self.username)  
		if u:
			msg = 'That user already exists.'
			self.render('userregistration.html', error_username = msg)
		else:
			u = User.register(self.username, self.password, self.email)
			u.put()

			self.login(u)
			self.redirect('/unit3/welcome')	

class Unit3Welcome(BlogHandler):
	def get(self):
		if self.user:
			self.render('welcome.html',username = self.user.name)
		else:
			self.redirect('/userregistration')			

class Login(BlogHandler):
	def get(self):
		self.render('login-form.html')

	def post(self):
		username = self.request.get('username')
		password = self.request.get('password')

		u = User.login(username, password)
		if u:
			self.login(u)
			self.redirect('/welcome')
		else:
			msg = 'invalid login'
			self.render('login.html',error = msg)

class Logout(BlogHandler):
	def get(self):
		self.logout()
		self.redirect('/signup')									


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
		self.render('newpost.html')

	def post(self):
		subject=self.request.get('subject')
		content= self.request.get('content')

		if subject and content:
			p=Blog(parent=blog_key(),subject=subject,content=content)
			p.put()
			x=str(p.key().id())
			#self.write('/blog / %s' % x)
			#self.redirect('/blog / %s' % x )
			self.redirect('/blog/%s'%x)
			#self.redirect(r'/blog/(\d+)>',PostHandler)
		else:
			error = "subject and content,please !"
			self.render("newpost.html",subject=subject,content=content,error=error)		


class PostHandler(BlogHandler):
	def get(self,blog_id):
		p=Blog.get_by_id(blog_id)
		if p:
			self.render('permalink.html',p=p)
		
		



#class MainPage(BlogHandler):

#	def render_naididit(self,blgtitle="",blgcontent="",error=""):
#		blog = db.GqlQuery("SELECT * FROM Blog ORDER BY created DESC")
#
#		self.render("naididit.html",blgtitle=blgtitle,blgcontent=blgcontent,error=error,blog=blog)
##
#	def get(self):	
		#self.write("front welcome page") 
#		self.render_naididit()
		#self.response.headers['Content-Type'] = 'text/plain'
		self.render("newpost.html")

#	def post(self):
#		NewPost(BlogHandler)

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

app=webapp2.WSGIApplication([('/',BlogFront),
							  ('/blog/?',BlogFront),
							  ('/blog/([0-9]+)',BlogPost),
							  #('/blog/[0-9]+)',PostHandler),
							  ('/welcome',Welcome),	
							  ('/blog/newpost',NewPost),
							  ('/userregistration',Register),
							  ('/unit3/welcome',Unit3Welcome),
							  ('/login',Login),
							  ('/logout',Logout),
							  ],
							  debug = True)				