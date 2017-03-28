######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
import time

#for image uploading
from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'secret string'

app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'password'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users") 
users = cursor.fetchall()

        
class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd 
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out') 

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html') 

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')  

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		first_name=request.form.get('first_name')
		last_name=request.form.get('last_name')
		dob=request.form.get('dob')
	except:
		print "couldn't find all tokens" #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print cursor.execute("INSERT INTO Users (email, password,first_name, last_name, dob) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')".format(email, password,first_name, last_name, dob))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=first_name, message='Account Created!')
	else:
		print "couldn't find all tokens"
		return flask.redirect(flask.url_for('register'))
	
def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)): 
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
    
    #end login code


def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	users = cursor.fetchall()
	final_list =[r[0] for r in users]
	return final_list

def getUserID():
	cursor = conn.cursor()
	cursor.execute("SELECT user_id from Users") 
	return cursor.fetchall()

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall()

def getUsersPhotosFromAlbum(uid,name):
        cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE album_name = '{0}' AND user_id= '{1}'".format(name,uid))
	return cursor.fetchall()

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]
	
def getUsersAlbums(uid):
        cursor = conn.cursor()
	cursor.execute("SELECT name FROM album WHERE user_id = '{0}'".format(uid))
	albums = cursor.fetchall()
	final_list =[r[0] for r in albums]
	return final_list

def getUsersFriends(email):
        cursor = conn.cursor()
        cursor.execute("SELECT user_1 FROM Friends WHERE user_2 = '{0}' UNION SELECT user_2 FROM Friends WHERE user_1 = '{0}'".format(email))
	friends = cursor.fetchall()
	final_list =[r[0] for r in friends]
	return final_list

def getUsersPhoto(user, album, photoid):
        cursor = conn.cursor()
        cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = (SELECT user_id FROM users WHERE email = '{0}') AND album_name ='{1}' AND picture_id ='{2}'".format(user,album,photoid)) 
	picture = cursor.fetchone()
	return picture

def getComments(picture_id):
        cursor = conn.cursor()
	cursor.execute("SELECT owner_id, text FROM Comment WHERE photo_id= '{0}'".format(picture_id))
 	return cursor.fetchall()

def getNumLikes(picture):
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(like_id) FROM Likes WHERE picture_id= '{0}'".format(picture))
        numlikes = int(cursor.fetchone()[0])
        return numlikes

def getPhotoId(img,user_id,album):
        cursor = conn.cursor()
	cursor.execute("SELECT picture_id FROM Pictures WHERE imgdata= '{0}' AND user_id = '{1}' AND album_name = '{2}'".format(img, user_id, album))
	photo_id = int(cursor.fetchone()[0])
 	return photo_id

def getTags(picture_id):
        cursor = conn.cursor()
	cursor.execute("SELECT tag FROM Tags WHERE picture_id = '{0}'".format(picture_id))
        tags = cursor.fetchall()
        tag_list =[r[0] for r in tags]
        return tag_list

def getLikers(picture_id):
        cursor = conn.cursor()
	cursor.execute("SELECT DISTINCT user_id FROM Likes WHERE picture_id = '{0}'".format(picture_id))
        likers = cursor.fetchall()
        final_list = []
        for liker in likers:
                final_list.append(str(liker[0]))
        return final_list

def getPicturesFromTag(tag):
        cursor = conn.cursor()
        cursor.execute("SELECT imgdata FROM Pictures WHERE picture_id IN (SELECT picture_id FROM tags WHERE tag = '{0}')".format(tag)) 
	return cursor.fetchall()
       

@app.route('/profile', methods=['GET', 'POST'])
@flask_login.login_required
def protected():
        if request.method == 'POST':
                uid = getUserIdFromEmail(flask_login.current_user.id)
                date = time.strftime("%Y/%m/%d")
                photo_id = '0'
                return render_template('profile.html', name=flask_login.current_user.id, message="Here's your profile", photos=getUsersPhotos(uid), all_friends=getUsersFriends(flask_login.current_user.id))
        else:
                uid = getUserIdFromEmail(flask_login.current_user.id)
                return render_template('profile.html', name=flask_login.current_user.id, message="Here's your profile", photos=getUsersPhotos(uid), all_friends=getUsersFriends(flask_login.current_user.id))


#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML 
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		album_name = request.form.get('album')
		photo_data = base64.standard_b64encode(imgfile.read())
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Pictures (imgdata, user_id, caption, album_name) VALUES ('{0}', '{1}', '{2}','{3}')".format(photo_data, uid, caption, album_name))
		conn.commit()
		if request.form.get('tags') is None or "":
                        pass
                else:
                        tags = request.form.get('tags')
                        all_tags = [value for value in tags.split(',')]
                        photo_id = getPhotoId(photo_data,uid,album_name)
                        email = flask_login.current_user.id
                        for tag in all_tags:
                                cursor = conn.cursor()
                                cursor.execute("INSERT INTO Tags (tag, picture_id, user_id, user_email) VALUES ('{0}', '{1}', '{2}','{3}')".format(tag, photo_id, uid, email))
                                conn.commit()                       
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid) )
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code 


#begin album creation code
@app.route('/createalbum', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
        if request.method == 'POST':
                uid = getUserIdFromEmail(flask_login.current_user.id)
                name = request.form.get('name')
                cursor = conn.cursor()
                date = time.strftime("%Y/%m/%d")
		cursor.execute("INSERT INTO Album (name, user_id, created) VALUES ('{0}', '{1}', '{2}' )".format(name,uid, date))
                conn.commit()
                return render_template('hello.html', name= flask_login.current_user.id, message='Album Created!')
        else:
                return render_template('createalbum.html')
#end album creation code

#userprofile code
@app.route('/userpage/<username>')
def userpage(username):
        uid = getUserIdFromEmail(username)
        photos = getUsersPhotos(uid)
        albums = getUsersAlbums(uid)
        return render_template('userpage.html', name= username, albums = albums)



#albumsforusers code
@app.route('/userpage/<username>/<album>')
def useralbums(username,album):
        uid = getUserIdFromEmail(username)
        photos = getUsersPhotosFromAlbum(uid,album)
        return render_template('albums.html', name= username, photos=photos, album=album)


#picturepage
@app.route('/userpage/<username>/<album>/<picture>', methods=['GET', 'POST'])
def userpicture(username,album,picture):
        if request.method == 'POST':
                owner_id = flask_login.current_user.id
                date = time.strftime("%Y/%m/%d")
                thephoto = getUsersPhoto(username, album, picture)
                tags = getTags(picture)
                if request.form.get('comment') is None or "":
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO Likes (user_id, picture_id) VALUES ('{0}', '{1}')".format(owner_id, picture))
                        conn.commit()
                else:
                        text = request.form.get('comment')
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO Comment (owner_id, photo_id, created, text, photo_owner) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}')".format(owner_id, picture, date, text, username))
                        conn.commit()
                allcomments = getComments(picture)
                numlikes = getNumLikes(picture)
                all_likers = getLikers(picture)
                return render_template('picture.html', name= username, album=album, photo=thephoto, comments=allcomments, likes= numlikes , tags=tags, likers=all_likers)
        else:
                thephoto = getUsersPhoto(username, album, picture)
                allcomments = getComments(picture)
                numlikes = getNumLikes(picture)
                tags = getTags(picture)
                all_likers = getLikers(picture)
                return render_template('picture.html', name= username, album=album, photo=thephoto, comments=allcomments, likes=numlikes,tags=tags, likers=all_likers)

#tagpage
@app.route('/<tag>')
def tagpage(tag):
        all_pictures = getPicturesFromTag(tag)
        return render_template('tag.html', photos = all_pictures, tag=tag)
        


#addfriends code
@app.route('/addfriend', methods=['GET', 'POST'])
@flask_login.login_required
def addfriend():
        if request.method == 'POST':
                user_1 = request.form.get('friend')
                user_2 = flask_login.current_user.id
                cursor = conn.cursor()
		cursor.execute("INSERT INTO Friends (user_1, user_2) VALUES ('{0}', '{1}')".format(user_1, user_2))
                conn.commit()
                return render_template('hello.html', name= flask_login.current_user.id, message='Friend added!')
        else:
                return render_template('addfriends.html', message='Add a friend!', username=getUserList())



#default page  
@app.route("/", methods=['GET'])
def hello():
        username = getUserList()
	return render_template('hello.html', message='Welcome to Photoshare', username=getUserList())

if __name__ == "__main__":
	#this is invoked when in the shell  you run 
	#$ python app.py 
	app.run(port=5000, debug=True)
