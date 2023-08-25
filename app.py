from flask import Flask, render_template, request, redirect, session
from cs50 import SQL
from helpers import login_required
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask("__name__")

db = SQL("sqlite:///webApp.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET"])
@login_required
def index():
    return render_template("index.html")

@app.route("/searchResults", methods=["GET", "POST"])
@login_required
def searchResults():

    if request.method == "POST":

        query = request.form.get("query")
        if not query:
            print("Query is void")

        return redirect("/")
    
    else:
        return render_template("results.html")
    
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        return redirect("/")
    
    else:
        return render_template("login.html")
    
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # Gets values passed by user
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # If any of those values are null, redirect to /register route
        if not username or not password or not confirmation:
            return redirect("/register")
        
        # If password does not match confirmation redirect to /register route
        if password != confirmation:
            return redirect("/register")
        
        # Checks if record with same username already exists, if yes redirect user
        row = db.execute("SELECT * FROM users WHERE username = ?;", username)
        if len(row) > 0:
            return redirect("/register")
        
        # Generate hash and insert new user into database
        hash_pw = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?);", username, hash_pw)

        return redirect("/")
    
    else:
        return render_template("register.html")