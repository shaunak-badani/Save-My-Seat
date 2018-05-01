from flask import Flask,render_template,request,url_for,redirect,session
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import URLSafeTimedSerializer,SignatureExpired
from flask_mail import Mail,Message
from flask.ext.uploads import UploadSet, configure_uploads, IMAGES
from sqlalchemy import exc
from functools import wraps
from movies import show,Movies,Appoint
from passlib.hash import pbkdf2_sha256
import movies,os,sys,listmovies

app = Flask(__name__)
app.register_blueprint(show)
photos = UploadSet('photos', IMAGES)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOADED_PHOTOS_DEST'] = 'static/images'
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT']=465
app.config['MAIL_USERNAME']='savemyseatitws@gmail.com'
app.config['MAIL_PASSWORD']='confirmemail'
app.config['MAIL_USE_TLS']=False
app.config['MAIL_USE_SSL']=True
configure_uploads(app, photos)
mail = Mail(app)	
s=URLSafeTimedSerializer('Thisisasecret')
db = SQLAlchemy(app)
app.secret_key = "my precious" #key to access user data on the server side


class PeopleReg(db.Model):
	__tablename__ = 'users'
	user_id = db.Column(db.Integer,primary_key = True)
	username = db.Column(db.String(200),nullable = False)
	email = db.Column(db.String(200),nullable = False)
	pswd = db.Column(db.String(10000),nullable = False)

def add_admin():
	admin = PeopleReg(username = "admin",email = "admin@gmail.com",pswd = pbkdf2_sha256.hash("itproj_2k18")) #bypass email confirmation here
	if PeopleReg.query.filter_by(username = "admin").first()==None:
		db.session.add(admin)
		db.session.commit()

def login_required(f):
	@wraps(f)
	def wrap(*args,**kwargs):
		if 'username' in session:
			return f(*args,**kwargs)
		else:
			return redirect(url_for('login'))
	return wrap

@app.route('/')
def hi():
	return render_template('ind.html')

@app.route('/register',methods = ['GET','POST'])
def register():
	return render_template('register.html')

@app.route('/add_movie',methods = ['GET','POST'])
@login_required	
def added_movie():
	if session['username'] != "admin":
		return render_template("unworthy.html")
	if request.method =="POST":
		file = request.files['pic']
		filename = None
		if 'pic' in request.files:
			filename = photos.save(request.files['pic'])
		movie = Movies(name = request.form['name'],cast = request.form['cast'],
			rat = int(request.form['rating']),lang = request.form['lang'], genre = request.form['genre'],
			img_link = filename,c_rating = int(request.form['c_rating']),
			avg_rating = int(request.form['avg_rating']),release_date = request.form['release_date'],
					duration = request.form['duration'])
		if Movies.query.filter_by(name = movie.name).first() != None:
			return render_template('unsuccessful.html',error = "Movie already exists!")
		db.session.add(movie)
		db.session.commit()
	return render_template('add_movie.html')

# REG CONFIRMATION

@app.route('/confirmation/<token>')
def reg(token):
	error = None
	try:	
		email=s.loads(token,salt='email-confirm',max_age=3600)
	except SignatureExpired:
		return render_template('registered.html',error = error)
	Person = PeopleReg(username = Variables.cur['username'],
		email = Variables.cur['email'],pswd = pbkdf2_sha256.hash(Variables.cur['pswd']))
	db.session.add(Person)
	db.session.commit()
	return render_template('registered.html',error = error)
	# return '<h1> The token works</h1>'

from movies import Variables

@app.route('/Confirmation',methods = ['GET','POST'])
def registered():
	error = None
	username,pswd,email = "","",""
	if request.method == 'POST':
		Variables.cur['username'],Variables.cur['pswd'] = request.form['username'],request.form['password']
		email,Variables.cur['email'] = request.form['e-mail'],request.form['e-mail']
		token=s.dumps(email,salt='email-confirm')
		if PeopleReg.query.filter_by(username = Variables.cur['username']).first() != None:
			error = "Username already taken. Please try another."	
		elif PeopleReg.query.filter_by(email = Variables.cur['email']).first() != None:
			error = "Email Id Already taken. Please try another!"
		else:
			msg=Message('Confirm Email',sender='savemyseatitws@gmail.com',recipients=[email])
			link=url_for('reg',token=token,_external=True)
			print(link)
			msg.body='Your link is {}. Click on it as it will get expire after 1 hr !'.format(link)
			mail.send(msg)
			return render_template('email_verify.html')	
		return render_template('registered.html',error = error)
	

@app.route('/logout')
@login_required
def logout():
	session.pop('username')
	return redirect(url_for('hi'))

@app.route('/login',methods = ['GET','POST'])
def login():
	error = None
	if request.method == 'POST':
		search = PeopleReg.query.filter_by(username = request.form['username']).first()
		if search == None:
			error = "Invalid Credentials. Please try again."
		else:
			a=request.form['password']
			if pbkdf2_sha256.verify(a,search.pswd):
				session['username'] = search.username
				return redirect(url_for('show.display_movie'))
			else:
				error = "Invalid Credentials. Please try again."
	return render_template('login.html',error = error)	

if __name__ == "__main__":
	db.create_all()	
	add_admin()
	app.run(debug = True)