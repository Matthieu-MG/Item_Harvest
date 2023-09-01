from flask import Flask, render_template, request, redirect, session, url_for
from cs50 import SQL
from helpers import login_required, getCurrency,  EbayFind, EtsyFind
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import requests
import json

load_dotenv()
# take environment variables from .env.

# print(getCurrency('Mauritius'))
# EbayFindByID('175811784059')
'''
legos = EbayFind('lego')
for lego in legos:
    print(lego['title'])
    print(lego['id'])
    print(lego['price'])
    print(lego['image'])

EbayFindByID(legos[0]['id'])
'''

app = Flask("__name__")

# Setting up database in app.py
db = SQL("sqlite:///webApp.db")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Used in development so that templates change on the page when their source code is changed
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

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

    # Gets user's history, to be used for autocomplete
    history = []
    user_history = db.execute("SELECT search FROM users_history WHERE user_id = ? ORDER BY id DESC LIMIT 5;", session["user_id"])

    if len(user_history) > 0:
        for search in user_history:

            _search = search['search']

            # If search is too long, truncate it
            if len(_search) > 23:
                _search = _search[:23]
                _search = f"{_search}..."

            history.append(_search)

    return render_template("index.html", history=history)


@app.route("/searchResults", methods=["GET"])
@login_required
def searchResults():

    # Gets query searches values
    query = request.args.get("query")
    if not query:
        return redirect("/")
    
    # If search if not already in the user search history, add it
    row = db.execute("SELECT * FROM users_history WHERE search = ? AND user_id = ?;", query, session["user_id"])
    if row != 1:
        db.execute("INSERT INTO users_history (search, user_id) VALUES (?, ?);", query, session["user_id"])

    # Search items via Ebay's Finding API
    s_results = EbayFind(query)

    return render_template("results.html", s_results=s_results)


@app.route("/add", methods=["POST"])
@login_required
def add():
    
    # Gets items added to wishlist
    items = request.get_json()
    items = items["wishlist"]

    # Iterates through all items that need to be added to wishlist
    for item in items:
        product = json.loads(item)

        '''A CHECK IN CASE USER TRIES TO ENTER SAME PRODUCT EITHER NOTIFY USER OR INCREASE QUANTITY ?'''
        row = db.execute("SELECT * FROM users_wishlist WHERE user_id = ? AND link = ? and title = ?"
                         , session["user_id"]
                         , product['link']
                         , product['title']
                    )
        
        # Checks if item is already in wishlist, if yes does not add it
        if len(row) > 0:
            print("Already in wishlist")
            continue

        # Add Item To Wishlist
        db.execute("INSERT INTO users_wishlist(user_id, title, price, retailer, link, img) VALUES (?, ?, ?, ?, ?, ?);"
                    ,session["user_id"]
                    ,product['title']
                    ,product['price']
                    ,product['retailer']
                    ,product['link']
                    ,product['img']
                )

    return redirect(url_for("wishlist"))


@app.route("/wishlist", methods=["GET"])
@login_required
def wishlist():

    # Gets all items from user's wishlist
    user_wishlist = db.execute("SELECT * FROM users_wishlist WHERE user_id = ?;", session["user_id"])

    # Renders wishlist page and passes in the user's wishlist
    return render_template("wishlist.html", user_wishlist=user_wishlist)
    

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        # Get values posted by user
        username = request.form.get("username")
        password = request.form.get("password")

        # If password or username is null
        if not password or not username:
            return redirect("/login")
        
        # Get user's record in database
        user_record = db.execute("SELECT * FROM users WHERE username = ?", username)
        # If returned record is null or greater than 2, redirect user to same page
        if len(user_record) != 1:
            print("USER DOES NOT EXIST")
            return redirect("/login")

        # If password hash in database does not match password posted, redirect user to login page
        if not check_password_hash(user_record[0]["hash"], password):
            print("INCORRECT PASSWORD")
            return redirect("/login")
        
        # Assigns session to the user
        session["user_id"] = user_record[0]["id"]

        return redirect("/")
    
    else:
        return render_template("login.html")
    

@app.route("/logout", methods=["GET"])
def logout():

    # Clears current session
    session.clear()

    # Returns to index/login route
    return redirect("/")


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