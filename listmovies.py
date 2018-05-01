from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from bs4 import BeautifulSoup
from movies import *
import sys,urllib,sys,os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class add:

	@staticmethod
	def make():
		i = 0
		url = "https://timesofindia.indiatimes.com/entertainment/latest-new-movies/english-movies"
		sauce = urllib.request.urlopen(url).read()
		soup = BeautifulSoup(sauce,'html.parser')

		db.create_all()
		if not os.path.isdir("./images"):
			os.system('mkdir images')

		for movie in soup.find_all('div',class_ = "mr_lft_box"):
			
			#TITLE:
			title = movie.find('h3')
			name = title.text
			# print(title.text)

			#CAST: STRING
			cast = movie.find('p',class_ = "castnames_wrapper")
			if cast != None:
				cast = cast.text.strip()

			# language = movie.find_all('div',class_ = "mrB10 clearfix")
			# LANGUAGE AND GENRE
			lpg = movie.find('small').find('br')
			languages = movie.find('small')
			genre = lpg.text.split("|")[0]
			try:
				rat = lpg.text.split("|")[1].strip()
			except IndexError as err:
				rat = None
			# print(rat)
			# print("GENRE:",genre) 	#Take care of IndexError as error while determining rating
			lang = languages.text[:languages.text.find(lpg.text)]
			# print("LANGUAGES:",lang)

			#IMGS:
			imgs = movie.find('img')
			link = imgs['src']
			basename = "-".join(title.text.split())
			img_link = basename	
			urllib.request.urlretrieve(link,'static/images/'+img_link)
			# print(fullfilename) 
			# print(link) #done!!!!

			#RATINGS:
			try:
				c_rating = movie.find('span',class_ = "crit_txt").find_next('span',class_="star_count")
				avg_rating = c_rating.find_next('span',class_ = "crit_txt").find_next('span',class_="star_count")
				c_rating = c_rating.text
				avg_rating = avg_rating.text	
				# print("Crtic Rating : ",c_rating.text)
				# print("User's Rating : ",avg_rating.text)
			except AttributeError as err:
				c_rating = None
				avg_rating = None
				# print("Not available")

			# DURATION AND DATE
			durationdate = movie.find('h4')
			a = durationdate.text.strip().split("|")
			release_date = a[0]
			try:
				duration = a[1].strip() #strip before saving
			except :
				duration = "NA"
			i = i + 1
			print("Fetching Movie : ",i)
			movie = Movies(name = name,cast = cast,lang = lang,
				genre = genre,rat = rat,img_link = img_link,c_rating = c_rating,
				avg_rating = avg_rating,release_date = release_date,duration = duration)
			db.session.add(movie)
			# Appoint.appoint_theatres(movie)

		db.session.commit()
if __name__ == "__main__":
	add.make()