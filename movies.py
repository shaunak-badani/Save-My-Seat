from flask import Flask,render_template,request,Blueprint,send_file,redirect,url_for,session,jsonify
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy 
from functools import wraps
import math,random,re,json
from io import BytesIO

show = Blueprint('show',__name__)
app = Flask(__name__)	
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


screens = db.Table('screens',
	db.Column('movie_id',db.Integer,db.ForeignKey('movie.movie_id')),
	db.Column('theatre_id',db.Integer,db.ForeignKey('theatre.theatre_id')),
	)
app.secret_key="my precious"

class Variables:
	cur = {}

class Appoint:	
	def appoint_movie(th):
		x = Movies.query.all()
		c = th.no_of_screens
		for i in range(1,c+1):
			th.movies.append(Movies.query.filter_by(movie_id = i).first())
		db.session.commit()

class Times:
	@staticmethod
	def string_time(a,b):
		if int(b/10) == 0:
			if int(a/10) == 0:
				return "0"+str(a) + ":" + "0" + str(b)
			return str(a) + ":"+ "0" + str(b)
		else:
			if int(a/10) == 0:
				return "0"+str(a) + ":" + str(b)
		return str(a) + ":" + str(b)

	@staticmethod
	def duration(a):
		a = a.lower()
		matchObj = re.match(r'(.*) hrs? (.*) mins?',a,re.M|re.I)
		m = int(matchObj.group(1))
		n = int(matchObj.group(2))
		return m*60 + n


	@staticmethod
	def generate_times(movie):
		c = random.randint(8,10)
		b = (random.randint(0,6)*10)%60
		try:
			d = Times.duration(movie.duration) + 30 #for cleaning
		except:
			d = 150
		a = []
		a.append(Times.string_time(c,b))
		for i in range(0,6):
			c = (c + math.trunc(int(d/60)))%24
			b = (b + d%60)%60
			a.append(Times.string_time(c,b))
		return a

class Movies(db.Model):
	__tablename__='movie'
	movie_id = db.Column(db.Integer,primary_key = True)
	name = db.Column(db.String(2000))
	cast = db.Column(db.String(2000))
	lang = db.Column(db.String(2000))
	genre = db.Column(db.Integer)
	rat = db.Column(db.Integer)
	img_link = db.Column(db.String(2000))
	c_rating = db.Column(db.Integer)
	avg_rating = db.Column(db.Integer)
	release_date = db.Column(db.String(100))
	duration = db.Column(db.String(100))
	cinemas = db.relationship('Theatres',secondary = screens,
		backref = db.backref('movies',lazy = 'dynamic'))	

class Theatres(db.Model):
	__tablename__ = 'theatre'
	theatre_id = db.Column(db.Integer,primary_key = True)
	name = db.Column(db.String(20))
	no_of_screens = db.Column(db.Integer)



class TheatreTimings(db.Model):
	__tablename__ = "theatretimings"
	id = db.Column(db.Integer,primary_key = True)
	movie_id = db.Column(db.Integer,db.ForeignKey("movie.movie_id"))
	theatre_id = db.Column(db.Integer,db.ForeignKey("theatre.theatre_id"))
	theatre = db.relationship("Theatres",foreign_keys = [theatre_id])
	timings = db.Column(db.String(200))
	movie = db.relationship("Movies",foreign_keys = [movie_id])



#MOVIES:
def login_required(f):
	@wraps(f)
	def wrap(*args,**kwargs):
		if 'username' in session:
			return f(*args,**kwargs)
		else:
			return redirect(url_for('login'))
	return wrap


@show.route('/Movies',methods=['GET'])
@login_required
def display_movie():
	movie = Movies.query.all()
	return render_template('movies.html',movies=movie)

@show.route('/Theatres',methods = ['GET','POST']) 
@login_required
def show_theatres():
	a = Movies.query.all()
	for x in a:
		if x.name in request.form:
			Variables.cur['movie'] = x
			break
	return render_template('theatres.html',movie = Variables.cur['movie'],
		th = Variables.cur['movie'].cinemas)
	# return "successful"

#THEATRES:
@show.route('/add_theatre',methods = ['GET','POST'])
@login_required
def added_theatre():
	if session['username'] != "admin":
		return render_template("unworthy.html")
	if request.method == "POST":
		th = Theatres(name = request.form['theatre'],
			no_of_screens = int(request.form['no_of_screens']))
		if Theatres.query.filter_by(name = th.name).first() != None:
			return "Unsuccessful" #Add unsuccessful page here.
		else:
			Appoint.appoint_movie(th)
			db.session.add(th)
			db.session.commit()
	return render_template('addtheatre.html')

#TIMINGS:
@show.route('/Timings',methods = ['GET','POST'])
@login_required
def show_timings():
	m = Theatres.query.all()
	for x in m:
		if x.name in request.form:
			Variables.cur['theatre'] = x
			break 
	try:
		a = Times.generate_times(Variables.cur['movie'])
		tt = TheatreTimings.query.filter_by(theatre = Variables.cur['theatre'],
			movie = Variables.cur['movie']) 
		if tt.first() == None:	
			new_timings = TheatreTimings(timings = ";".join(a))
			new_timings.movie,new_timings.theatre = Variables.cur['movie'],Variables.cur['theatre']
			db.session.add(new_timings)
			db.session.commit()
			Variables.cur['times'] = a
		else:
			Variables.cur['times'] = tt.first().timings.split(";")
	except KeyError :
		return redirect(url_for('show.display_movie'))
	return render_template('timings.html',times = Variables.cur['times'])


#SCREENS:

@login_required
@show.route('/screens',methods = ['GET','POST'])
def sc():
	try:
		for x in Variables.cur['times']:
			if x in request.form:
				Variables.cur['timing'] = x
	except KeyError:
		return redirect(url_for('show.display_movie'))
	return redirect(url_for('show.screens'))

from app import PeopleReg
class Seats(db.Model): 
	__tablename__ = 'seats'
	id = db.Column(db.Integer,primary_key = True)
	user = db.Column(db.String(200))
	row_no = db.Column(db.Integer,nullable = False)
	column_no = db.Column(db.Integer,nullable = False)
	mov_id = db.Column(db.Integer,db.ForeignKey('movie.movie_id'))
	booked = db.Column(db.Boolean)
	th_id = db.Column(db.Integer,db.ForeignKey('theatre.theatre_id'))
	timing = db.Column(db.String(20))
	movie = db.relationship("Movies",foreign_keys = [mov_id])
	theatre = db.relationship("Theatres",foreign_keys = [th_id])


@show.route('/Screens',methods = ['GET','POST'])
@login_required
def screens():
	tempt,temps = [],[]
	try:
		if request.method == "POST":
			no = None
			for x in range(8):
				for y in range(9):
					if str(x*9 + y) in request.form:
						no = x*9 + y
						break
			if no == None:
				print("WTF")
			seat = Seats(
				row_no = math.floor(no/9), column_no = no%9,booked = False)
			seat.movie = Variables.cur['movie']
			seat.theatre = Variables.cur['theatre']
			seat.timing = Variables.cur['timing']
			db.session.add(seat)
			db.session.commit()
			
			tempt = []
			
			seats = Seats.query.filter_by(movie = Variables.cur['movie'],theatre = Variables.cur['theatre'],
				timing = Variables.cur['timing'],booked = False)
			for x in seats:
				temps.append((x.row_no,x.column_no))
			print(tempt)
			print(temps)
		taken = Seats.query.filter_by(movie = Variables.cur['movie'],theatre = Variables.cur['theatre'],
				timing = Variables.cur['timing'],booked = True)
		for x in taken:
				tempt.append((x.row_no,x.column_no)) 
		return render_template('screens2.html',
			no_of_columns = 9,no_of_rows = 8,taken = tempt,seats = temps)
	except KeyError:
		return redirect(url_for('show.display_movie'))
	

@show.route('/Checkout',methods = ['GET','POST'])
def checkout():
	a,b = [],[]
	print("getting there")
	if request.method == 'POST':
		print("here's where the problem is")
		try:
			x = request.form.to_dict() #delete
			a,b = x["js_data"],x["col_nos"]
			a,b = a.strip('[').strip(']').split(','),b.strip('[').strip(']').split(',')
			print(x,a,b,type(a),type(b))
		except KeyError as err:
			print("Not possible" + str(err))
	print("almost there")
	c = []
	for i in range(len(a)):
		new_seat = Seats(user = session['username'],timing = Variables.cur['timing'],
			row_no = int(a[i]),column_no = int(b[i]),booked = False)
		new_seat.movie,new_seat.theatre = Variables.cur['movie'],Variables.cur['theatre']
		db.session.add(new_seat)
	db.session.commit()
	return jsonify()
	# print("At this point i'm like seriously going WTF.")

@show.route('/checkout')
def check():
	a = Seats.query.filter_by(movie = Variables.cur['movie'],theatre = Variables.cur['theatre'],
		timing = Variables.cur['timing'],booked = False)
	c = []
	for x in a:
		x.booked = True
		c.append(("ABCDEFGHIJKLMNOPQRSTUVWXYZ"[x.row_no],x.column_no))
	return render_template("checkout.html",movie = Variables.cur['movie'],
		theatre = Variables.cur['theatre'],timing = Variables.cur['timing'],b = c)

#Bookings
@show.route('/Bookings')
def bookings():
	c = []
	x = []
	m = Movies.query.all()
	for i in m:
		seat = Seats.query.filter_by(user = session['username'],movie = i)
		if seat.first() !=None :
			c.append(seat)
	return render_template('bookings.html',seats = c)

db.create_all()
if __name__ == '__main__':
	app.run(debug = True)