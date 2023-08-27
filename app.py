from flask import Flask, render_template, request, redirect, session, url_for
from cs50 import SQL
from helpers import login_required
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash

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
    return render_template("index.html")


@app.route("/searchResults", methods=["GET"])
@login_required
def searchResults():

    # Gets query searches values
    query = request.args.get("query")
    if not query:
        return redirect("/")

    # Search database for items that contains the query passed in in their item name
    s_results = db.execute("SELECT * FROM inventory WHERE item_name LIKE ?", "%" + query + "%")

    # Makes retailers to upper (TO BE CHANGED)
    for result in s_results:
        result["retailer"] = result["retailer"].upper()

    return render_template("results.html", s_results=s_results)


@app.route("/add", methods=["POST"])
@login_required
def add():
    
    # Gets items added to wishlist
    items = request.get_json()
    print(items)
    items = items["wishlist"]

    # Iterates through all items added to wishlist
    for item in items:

        # Checks if abnormal item id was passed from client side (item id not in database), and returns in that case
        row = db.execute("SELECT * FROM inventory WHERE id = ?", item)
        if len(row) != 1:
            print("ABNORMAL ID PASSED IN")
            return redirect(url_for('index'))
        
        # If user already has that item, does not add it and goes to next item
        exist = db.execute("SELECT * FROM users_wishlist WHERE item_id = ? AND user_id = ?", item, session["user_id"])
        if len(exist) > 0:
            print("Already Exists In Wishlist")
            continue

        # Else inserts new items to user's wishlist
        db.execute("INSERT INTO users_wishlist(item_id, user_id) VALUES (?, ?)", item, session["user_id"])

    return redirect(url_for("wishlist"))


@app.route("/wishlist", methods=["GET"])
@login_required
def wishlist():

    # Gets all items from user's wishlist
    user_wishlist = db.execute("SELECT * FROM inventory WHERE id IN (SELECT item_id FROM users_wishlist WHERE user_id = ?);", session["user_id"])

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