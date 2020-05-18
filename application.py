import os

from flask import Flask, session,render_template,request
import datetime
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
    return render_template("index.html", message="Welcome !!")


@app.route("/register", methods=["POST","GET"])
def register():
    # Get form information.
    if request.method == "POST":
        name = request.form.get("name")
        password = request.form.get("password")
        db.execute("INSERT INTO USERS (name, password, MEMBERSHIP_SINCE ) VALUES (:name, crypt(:password, gen_salt('bf')),:curr_date)",
            {"name": name, "password": password, "curr_date": datetime.date.today()})
        db.commit()
        return render_template("success.html", message="You have successfully Registered.")
    if request.method == "GET":
        return render_template("signup.html")
        
@app.route("/login", methods=["POST","GET"])
def login():
    if request.method == "POST":
        name = request.form.get("name")
        session['name'] = request.form['name']
        password = request.form.get("password")
           
        if db.execute("SELECT * FROM USERS WHERE name = :name AND password = crypt(:password, password)", {"name": name,"password": password}).rowcount == 0:
            return render_template("error.html", message="User Name and password doesn't exist.")
                
        if db.execute("SELECT * FROM USERS WHERE name = :name AND password = crypt(:password, password)", {"name": name,"password": password}).rowcount == 1:
            return render_template("BookReview.html", message="Login Successul.")        
                
    if request.method == "GET":
        return render_template("login.html")

@app.route("/bookreview")
def bookreview():
    if request.method == "GET":
        return render_template("BookReview.html", message="Welcome !!")
    if request.method == "POST":
        return render_template("BookReview.html", message="Welcome !!")    

@app.route("/searchbook", methods=["POST","GET"])
def searchbook():
    if request.method == "POST":
        BookName = request.form.get("BookName")
        formatBookName = "%{}%".format(BookName)       
        
        if db.execute("select * from books where LOWER(isbn) like :BookName OR LOWER(title) like :BookName OR LOWER(author) like :BookName", {"BookName": formatBookName}).rowcount == 0:
            return render_template("error.html", message="No Book details exist.")

        Books_found=db.execute("select * from books where LOWER(isbn) like :BookName OR LOWER(title) like :BookName OR LOWER(author) like :BookName", {"BookName": formatBookName}).fetchall()
        return render_template("BookDetails.html", Booksdetails=Books_found)        
                
    if request.method == "GET":
        return render_template("BookReview.html")

@app.route("/logout")
def logout():
    session.pop('username', None)
    return render_template("index.html", session=session)
        
if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)
    
    
    