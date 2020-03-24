from flask import Flask, render_template, request, Response, url_for, session, redirect, g, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import exists
import pandas as pd #for the reccomendation
import numpy as np 
from scipy.sparse.linalg import svds
import json
import os  #for random secret key



app = Flask(__name__) #initiate the app
app.secret_key = os.urandom(24) #secret key needed for the sessions

app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
engine = 'sqlite:///db.sqlite3' #used to read data with python
app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///db.sqlite3' #path to the local database, can also be an online path
db = SQLAlchemy(app) #set up connection to the db 

class Ratings(db.Model):#inherits from db and it represents the table
    id = db.Column(db.Integer,primary_key=True)
    userid = db.Column(db.Integer,db.ForeignKey('users.userid'))
    bookid = db.Column(db.Integer,db.ForeignKey('books.bookid'))
    rating = db.Column(db.Float)

class Users(db.Model):
    __table_args__={'sqlite_autoincrement': True}
    userid = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(15),unique=True)
    password = db.Column(db.String(30))

class Books(db.Model):
    bookid = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(100),unique=True)
    genres = db.Column(db.String(100))




@app.route("/addRating", methods=["POST"])
def addRating():
    user = Users.query.filter_by(username=g.user).first()
    new_rating = Ratings(userid=user.userid,bookid=request.form['bookid'],rating= request.form['rating'])
    db.session.add(new_rating)
    db.session.commit()

    return "Done",201

@app.route("/getBooks", methods=["GET"])
def getBooks():
    books = Books.query.all()
    jsonBooks = []
    for book in books:
        jsonBooks.append(
            {
                "bookid":book.bookid,
                "title":book.title,
                "genres":book.genres
            }
        )
    return jsonify(books=jsonBooks)

@app.route("/getBooksUser", methods=["GET"])
def getBooksUser():
    user = Users.query.filter_by(username=g.user).first()
    books = Books.query.all()
    ratings = Ratings.query.filter_by(userid=user.userid).all()
    jsonBooks = []
    for book in books:
        rating = Ratings.query.filter_by(userid=user.userid,bookid=book.bookid).first()
        jsonBooks.append(
                    {
                        "bookid":book.bookid,
                        "title":book.title,
                        "genres":book.genres,
                        "rating":rating.rating if rating else None
                    }
                )        
    return jsonify(books=jsonBooks)
@app.route('/addBook/<title>/<genres>')
def addBook(title,genres):
    book = Books(title=title,genres=genres)
    db.session.add(book) #add the row
    db.session.commit()#update the database
    return "<h1>Book has been Added</h1>"

@app.route("/account",methods=["GET","POST"])
def account():
    if request.method=="POST":
        if request.form['type']=="change":
            user = Users.query.filter_by(username=g.user).first() #get the username of the active user
            new_username = request.form['username']
            ret = db.session.query(Users.userid).filter_by(username=request.form['signinUsername']).scalar() is not None
            if ret:
                flash("This username is taken by another user")
                return render_template('dash.html')
            else:
                user.username = new_username
                db.session.commit()
                session.pop('user',None) #drop the session every time the user wishes to login
                session['user'] = new_username #add the user to the session 
                return "Username Updated",201
        else:
            user = Users.query.filter_by(username=g.user).first()
            new_pass = request.form['newPass']
            old_pass = request.form['oldPass']
            if old_pass==user.password:
                user.password = new_pass 
                db.session.commit()
                return jsonify(msg="Your password has been updated")
            else:
                return jsonify(msg="Your old password in incorrect")

    else:
        if g.user:
            return render_template('dash.html')
        return redirect(url_for("index"))


@app.route('/',methods=["GET","POST"])
def index():
    if request.method=="POST":
        session.pop('user',None) #drop the session every time the user wishes to login
        formType = request.form['type']
        if formType == "login":
            #compare the password here and continiue to set the session 
            user = Users.query.filter_by(username=request.form['loginUsername']).first()
            if user: #check if user exists
                if request.form['loginPassword'] == user.password: #check if the password is correct
                    session['user'] = user.username #add the user to the session 
                    return redirect(url_for('protected'))
                else:
                    flash("The username or password is wrong") #the password is wrong so it returns this message
                    return (render_template('index2.html'))
            else:
                flash("The username or password is wrong")#the username doesn't exist so it returns this message
                return (render_template('index2.html'))
        else:
            ret = db.session.query(Users.userid).filter_by(username=request.form['signinUsername']).scalar() is not None
            if ret: #username exists so account cannot be created
                flash("This username already exists")
                return (render_template('index2.html'))
            else: #create account
                username = request.form['signinUsername']
                user = Users(username=username,password=request.form['signinPassword'])
                db.session.add(user) #add the row
                db.session.commit()#update the database
                session['user'] =  username#add the user to the session 
                return redirect(url_for('protected'))
            #else it will be a sign in, need to check for valid fields and username not existing in database already

    return render_template('index2.html')




@app.route("/signup",methods=["GET","POST"])
def signup():
    if request.method=="POST":
        ret = db.session.query(Users.userid).filter_by(username=request.form['signupUsername']).scalar() is not None
        if ret: #username exists so account cannot be created
            flash("This username already exists")
            return (render_template('signup.html'))
        else: #create account
            username = request.form['signupUsername']
            user = Users(username=username,password=request.form['signupPassword'])
            db.session.add(user) #add the row
            db.session.commit()#update the database
            session['user'] =  username#add the user to the session 
            return redirect(url_for('protected'))
    return render_template("signup.html")

@app.route("/protected")
def protected(): #for it to be password protected make sure the user has an active session before they can use this page
    #here use the session to get the reccomendations
    if g.user:
        return render_template('protected.html',username=g.user)
    return redirect(url_for("index"))


@app.route("/getReccs",methods=["GET"])
def getReccs():
    user = Users.query.filter_by(username=g.user).first()
    ratingsdf, reccsdf = reccomendations(user.userid)
    ratings = ratingsdf.to_dict('records')
    reccs = reccsdf.to_dict('records')
    return jsonify(ratings=ratings,reccs=reccs)
@app.before_request
def before_request():
    g.user = None #track a single person by generating a global thread assigned to them
    if 'user' in session:
        g.user = session['user']

@app.route("/getsession")
def getsession():
    if 'user' in session:
        return session['user']
    return "Not Logged In"

@app.route("/logout")
def dropsession():
    session.pop('user',None) #check if user is in session first to avoid errors
    return redirect(url_for("index"))

@app.route("/deleteAcc",methods=["POST"])
def deleteAcc():
    if g.user:
        user = Users.query.filter_by(username=g.user).first()
        db.session.delete(user)
        db.session.commit()
        dropsession()
        return "Deleted",201
    else:
        return jsonify(msg="User not in session"),403

def reccomendations(userid):
    user_row_number = userid-1
    #get the ratings and the books from sql to pandas dataframes
    no_users = db.session.query(Users).count()
    ratings_df = pd.read_sql_query('SELECT * FROM ratings;',engine)#might take the userid out: WHERE userid='+str(userid)
    books_df =  pd.read_sql_query('SELECT * FROM books;',engine)
    #prepare the data for SVD
    rdf = ratings_df.pivot(index='userid',columns='bookid',values='rating').fillna(0)
    r = rdf.values #meant to be as_matrix() but its going to be removed so use .values instead
    user_ratings_mean=np.mean(r,axis=1)
    r_demeaned = r - user_ratings_mean.reshape(-1,1) #ratings formatted and normalized
    U, sigma, Vt = svds(r_demeaned,min(3,no_users-1)) #need to have populated database so it doesnt error out on rank k 
    sigma = np.diag(sigma)

    all_user_pred = np.dot(np.dot(U,sigma),Vt)+user_ratings_mean.reshape(-1,1)
    preds_df = pd.DataFrame(all_user_pred,columns=rdf.columns)
    sorted_user_preds = preds_df.iloc[userid-1].sort_values(ascending=False) #get and sort specific users predictions

    user_data = ratings_df[ratings_df.userid==userid]
    num_recommendations = min(3,books_df.shape[0]-user_data.shape[0])
    user_full = (user_data.merge(books_df,how='left',left_on='bookid',right_on="bookid").sort_values(['rating'],ascending=False))#user data and movie information, useful for sending them to front end

    reccs = (books_df[~books_df['bookid'].isin(user_full['bookid'])].
         merge(pd.DataFrame(sorted_user_preds).reset_index(), how = 'left',
               left_on = 'bookid',
               right_on = 'bookid').
         rename(columns = {user_row_number: 'Predictions'}).
         sort_values('Predictions', ascending = False).
                       iloc[:num_recommendations, :-1]
                      )
    return user_full, reccs #return both the ratings with the titles added and the reccomendations



if __name__ == '__main__':
    app.run(debug=True)