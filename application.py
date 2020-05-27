import os

from flask import Flask, session,render_template,request,redirect,url_for
import datetime,requests
from datetime import date
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    session.pop('emailid', None)
    return render_template("index.html", session="Welcome !!")


@app.route("/register", methods=["POST","GET"])
def register():
    
    # Get form information.
    if request.method == "POST":
        emailid = request.form.get("emailid")
        name = request.form.get("name")
        password = request.form.get("password")
        db.execute("INSERT INTO USERS (EMAILID, name, password, MEMBERSHIP_SINCE ) VALUES (:emailid, :name, crypt(:password, gen_salt('bf')),:curr_date)",
            {"emailid": emailid, "name": name, "password": password, "curr_date": datetime.date.today()})
        db.commit()
        return render_template("success.html", message="You have successfully Registered.")
    if request.method == "GET":
        return render_template("signup.html")
        
@app.route("/login", methods=["POST","GET"])
def login():
    if request.method == "POST":
        emailid = request.form.get("emailid")
        session['emailid'] = request.form['emailid']
        password = request.form.get("password")
           
        if db.execute("SELECT * FROM USERS WHERE EMAILID = :EMAILID AND password = crypt(:password, password)", {"EMAILID": emailid,"password": password}).rowcount == 0:
            return render_template("error.html", message="User Name and password doesn't exist.")
                
        if db.execute("SELECT * FROM USERS WHERE EMAILID = :EMAILID AND password = crypt(:password, password)", {"EMAILID": emailid,"password": password}).rowcount == 1:
            session['logged_in'] = True
			
            return render_template("BookReview.html", message='Logged in as: ' + session['emailid'] + " successfully" )        
            
    if request.method == "GET":
        #response=render_template("login.html")
        #response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')
        return render_template("login.html")

@app.route("/bookreview")
def bookreview():
    if request.method == "GET":
        return render_template("BookReview.html", message="Welcome !!")
    if request.method == "POST":
        return render_template("BookReview.html", message="Welcome !!")
    
@app.route("/bookreview_search/<int:book_id>", methods=["POST","GET"])
def bookreview_search(book_id):
    """List details about a Book."""
    if not session.get('logged_in'):
        print("Not logged in")
        return redirect(url_for('login'))
    else:
        global review_rating
        global isbn_no
        # Make sure Book exists.
        book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
     
        if book is None:
            return render_template("error.html", message="No such book.")

        # Get all book details.
        book_details = db.execute("SELECT * FROM books WHERE id = :id",
            {"id": book_id}).fetchall()
        # Make sure Book exists.

        
        if book_details is None:
            book_details="No Book Exist"
        
        #book_review = db.execute("SELECT * FROM REVIEW WHERE book_id = :id", {"id": book_id}).fetchall()
        if db.execute("SELECT * FROM REVIEW WHERE book_id = :id", {"id": book_id}).rowcount == 0: 
            review_rating_msg="No Rating Exist"
        else:
            review_rating = db.execute("select book_id,avg(rating) from review where book_id=:id group by book_id",
                {"id": book_id}).fetchone()
            review_rating_msg=review_rating.avg
        loggedinas=session['emailid']
        
        user_details=db.execute("SELECT * FROM USERS WHERE EMAILID = :EMAILID", 
            {"EMAILID": loggedinas}).fetchall()
        
        isbn_no= db.execute("SELECT isbn FROM books WHERE id = :id",
            {"id": book_id}).fetchall()
            
        res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "8IscQCdcmYRmqNtnP27kTQ", "isbns": isbn_no})
        if res.status_code != 200:
            raise Exception("ERROR: API request unsuccessful.")
        Goodreads_res=res.json()
     #   Goodreads_res=Goodreads_review['books']['average_rating']
     #   return render_template("SubmitReview.html", Booksdetails=book_details,  review_rating=review_rating_msg, Goodreads_res=Goodreads_res)    
        return render_template("SubmitReview.html", user_details=user_details, Booksdetails=book_details,  review_rating=review_rating_msg, Goodreads_res=Goodreads_res)
        
@app.route("/searchbook", methods=["POST","GET"])
def searchbook():
    if not session.get('logged_in'):
        print("Not logged in")
        return redirect(url_for('login'))
    else:
        if request.method == "POST":
            BookName = request.form.get("BookName")
            formatBookName = "%{}%".format(BookName)       
            
            if db.execute("select * from books where LOWER(isbn) like :BookName OR LOWER(title) like :BookName OR LOWER(author) like :BookName", {"BookName": formatBookName}).rowcount == 0:
                return render_template("BacktoSearch.html", message="No Book details exist.")

            Books_found=db.execute("select * from books where LOWER(isbn) like :BookName OR LOWER(title) like :BookName OR LOWER(author) like :BookName", {"BookName": formatBookName}).fetchall()
            return render_template("BookDetails.html", Booksdetails=Books_found)        
                    
        if request.method == "GET":
            return render_template("BookReview.html",message='Logged in as: ' + session['emailid'] )

@app.route("/logout")
def logout():
    loggedoutfrom=session['emailid']
    session.pop('emailid', None)
    session['logged_in'] = False
    session.clear()  
    ### Added to clear session. 
    return render_template("index.html", session='Logged out as User: ' + loggedoutfrom )

@app.after_request
def after_request(response):
    response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')
    redirect("index.html")
    return response

@app.route("/submit_review", methods=["POST","GET"])
def submit_review():
    if not session.get('logged_in'):
        print("Not logged in")
        return redirect(url_for('login'))
    else:
        if request.method == "GET":
            return render_template("success.html", message="Inside Submt_review !!")
        if request.method == "POST":
            rating_points = request.form.get("rating_points")
            review_comments = request.form.get("review_comments")
            user_id = request.form.get("user_id")
            user_name = request.form.get("user_name")        
            book_id = request.form.get("book_id")
            book_isbn = request.form.get("book_isbn") 
            db.execute("INSERT INTO review (book_id , book_isbn , user_id , user_name , rating , review_comments , created_at  ) VALUES (:book_id, :book_isbn, :user_id,:user_name,:rating , :review_comments,:curr_time)",
                {"book_id": book_id, "book_isbn": book_isbn, "user_id": user_id, "user_name": user_name, "rating": rating_points,"review_comments": review_comments, "curr_time": datetime.datetime.utcnow()})
            db.commit()
            return render_template("BacktoSearch.html", message="You have successfully Registered the Review.")



    
if __name__ == "__main__":
    db.create_all()
    app.debug = True
    app.run()
    app.run(debug = True)