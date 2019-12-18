from flask import Flask, render_template, request, Response, url_for, session, redirect, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm 
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from datetime import datetime
import sys
import os 
app = Flask(__name__) #initiate the app
app.secret_key = os.urandom(24) #secret key needed for the sessions

app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///db.sqlite3' #path to the local database, can also be an online path
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class Ratings(db.Model):#inherits from db and it represents the table
    id = db.Column(db.Integer,primary_key=True)
    userid = db.Column(db.Integer,db.ForeignKey('users.userid'))
    bookid = db.Column(db.Integer,db.ForeignKey('books.bookid'))
    rating = db.Column(db.Float)

class Users(db.Model):
    userid = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(15),unique=True)
    password = db.Column(db.String(50))

class Books(db.Model):
    bookid = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(100),unique=True)
    genres = db.Column(db.String(200))


class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
@app.route('/<userid>/<bookid>/<rating>')
def rate(userid,bookid,rating):
    rating = Ratings(userid=userid,bookid=bookid,rating=rating)#instantiate it with them, don't pass the primary key as it is not needed
    db.session.add(rating) #add the row
    db.session.commit()#update the database
    
    return "<h1>Rating Added</h1>"

@app.route('/<userid>')
def get_user(userid):
    ratings = Ratings.query.filter_by(userid=userid).first() #need to change to all to get the books

    return 'The books rated by the user are {}'.format(ratings.bookid) #nned to change so it get the book ids and then gets the book titles 
@app.route('/',methods=["GET","POST"])
def index():
    if request.method=="POST":
        session.pop('user',None) #drop the session every time the user wishes to login
        #compare the password here and continiue to set the session 
        givenUsername = request.form['username']

        if request.form['username']
        if request.form['password']=="password":
            session['user'] = request.form['username']
            return redirect(url_for('protected'))
    return render_template('index2.html')


@app.route("/protected")
def protected(): #for it to be password protected make sure the user has an active session before they can use this page
    #here use the session to get the reccomendations
    if g.user:
        return render_template('protected.html',username=g.user)
    return redirect(url_for("index"))

@app.before_request
def before_request():
    g.user = None #track a single person by generating a global thread assigned to them
    if 'user' in session:
        g.user = session['user']
@app.route('/receiver', methods = ['POST'])
def worker():
	# read json + reply
    data = request.get_json()
    result = ''
    for item in data:
        # loop over every row
        result += str(item['make']) + '\n'

    return result
@app.route("/getsession")
def getsession():
    if 'user' in session:
        return session['user']
    return "Not Logged In"

@app.route("/dropsession")
def dropsession():
    session.pop('user',None) #check if user is in session first to avoid errors
    return "Dropped!"
@app.route('/ouput')
def output():
    return render_template('data.html',results=[
        {
            "UserID":"Chris",
            "BookID":"Good Book",
            "Rating":"5/5"
        }
    ])

if __name__ == '__main__':
    app.run()