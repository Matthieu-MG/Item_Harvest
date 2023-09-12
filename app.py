from flask import Flask, render_template, request, redirect, session, url_for
from cs50 import SQL
from helpers import login_required, EbayFind, getLocalCurrency, formatPrice, getCountryByIP, refreshExchangeRates
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
import requests
import json

# take environment variables from .env.
load_dotenv()

app = Flask("__name__")

app.jinja_env.filters["formatPrice"] = formatPrice

# Setting up database in app.py
db = SQL("sqlite:///webApp.db")


app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Used in development so that templates change on the page when their source code is changed
# app.config["TEMPLATES_AUTO_RELOAD"] = True
# app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Starts background task scheduler, to refresh exchange rates at 8AM and 8PM
refreshExchangeRates()

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

            s = search['search']
            display = s

            # If search is too long, truncate it for the display
            if len(s) > 23:
                display = s[:23]
                display = f"{display}..."

            _search = {
                'search': s,
                'display': display
            }

            # Add to history list
            history.append(_search)

    return render_template("index.html", history=history)


@app.route("/userLocation", methods=["POST"])
@login_required
def userLocation():

    # Gets user's location from client-side
    response = request.get_json()

    try:

        # Gets country via ip address sent from client-side
        country = getCountryByIP(response['ip_address']['ip'])

        # If no country was returned
        if not country:
            print("Unable To Get Country From Coordinates")

        # Else assign that country to the user's session
        else:
            session['user_country'] = country

    # Handles exception in case longitude and latitude keys are not in the JSON data
    except KeyError:
        print("Invalid Data Received")

    return redirect("/")


@app.route("/searchResults", methods=["GET","POST"])
@login_required
def searchResults():

    # Gets user's url links for items in user's wishlist
    items_in_wishlist = db.execute("SELECT link FROM users_wishlist WHERE user_id = ?;", session['user_id'])

    # List to store all formatted urls of items in user's wishlist
    urls_in_wishlist = []
    try:
        for url in items_in_wishlist:
            # Format urls to match buttons id in results.html's DOM
            link = url['link']
            link = link.replace("\\", "\\\\")
            urls_in_wishlist.append(f"button{link}")
    except KeyError:
        print('No Key "link" in list')
    
    # Tries to make list into correct JSON format for parsing
    try:
        urls_in_wishlist = json.dumps(urls_in_wishlist)

    # Catches error that may occur when Parsing
    except (json.decoder.JSONDecodeError, TypeError) as e:
        print(f"An error occurred while serializing: {e}")

    if request.method == 'POST':
        # Get existing search results
        existing_search = request.form.get("sortPrice")
        sortType = request.form.get("sortType")

        # Get sorting type (asc or desc), default to ascending in case client did not specify or change radios' names on client-side
        reverse = False
        if sortType:
            if sortType == "ascending":
                reverse = False
            elif sortType == "descending":
                reverse = True

        if existing_search:
            try:
                # Sanitize string to load into JSON format
                existing_search = existing_search.replace("'",'"')
                existing_search = existing_search.replace("\\","\\\\")

                # Load search results into search as a list of dictionaries
                search = json.loads(existing_search)
                
                try:
                    # Sort search based on price value and renders to webpage
                    s_results = sorted(search, key=lambda x: float(x['price']), reverse=reverse)
                    currency = getLocalCurrency([])['currency']
                    return render_template("results.html", s_results=s_results, currency=currency, urls_in_wishlist=urls_in_wishlist)
                
                except KeyError:
                    return redirect("/")
            
            except json.decoder.JSONDecodeError:
                return redirect("/")
            
        return redirect("/")

    # Gets query searches values
    query = request.args.get("query")
    if not query:
        return redirect("/")
    
    # Checks whether user allows for their history to be recorded
    recordHistory = db.execute("SELECT record_history FROM users WHERE id = ?;", session['user_id'])
    try:
        # If user allows it, record search query
        if len(recordHistory) == 1 and recordHistory[0]['record_history'] == 1:
            
            # If search is not already in the user search history, add it
            row = db.execute("SELECT * FROM users_history WHERE search = ? AND user_id = ?;", query, session["user_id"])
            if len(row) < 1:
                db.execute("INSERT INTO users_history (search, user_id) VALUES (?, ?);", query, session["user_id"])

    except KeyError:
        print('Could not get record value')

    # Search items via Ebay's Finding API
    s_results = EbayFind(query)
    
    # If user provided their location, provide local currency prices, else provides prices in USD
    results_details = getLocalCurrency(s_results)

    currency = results_details['currency']
    s_results = results_details['results']

    return render_template("results.html", s_results=s_results, currency=currency, urls_in_wishlist=urls_in_wishlist)


@app.route('/enableDisableHistory', methods=["POST"])
@login_required
def disableHistory():

    ''' Enables/Disables user's history '''

    # Check whether user has their history recorded enabled or disabled
    isEnabled = db.execute("SELECT record_history FROM users WHERE id = ?;", session['user_id'])
    if len(isEnabled) == 1:
        # If enabled, disable it
        if isEnabled[0]['record_history'] == 1:
            db.execute("UPDATE users SET record_history = 0 WHERE id = ?;",session['user_id'])
        # If disabled, enable it
        else:
            db.execute("UPDATE users SET record_history = 1 WHERE id = ?;",session['user_id'])

    return render_template('settings.html')


@app.route('/directAdd', methods=['POST'])
@login_required
def directAdd():
    ''' Route to directly add an item to the wishlist '''
    item = request.get_json()

    try:
        item = item['item']
        print(item)
        item = json.loads(item)
        
        try:
            '''A CHECK IN CASE USER TRIES TO ENTER SAME PRODUCT EITHER NOTIFY USER OR INCREASE QUANTITY ?'''
            row = db.execute("SELECT * FROM users_wishlist WHERE user_id = ? AND link = ? and title = ?"
                            , session["user_id"]
                            , item['link']
                            , item['title']
                        )
            
            # Checks if item is already in wishlist, if yes does not add it
            if len(row) > 0:
                print("Already in wishlist")

            else:
                # Add Item To Wishlist
                db.execute("INSERT INTO users_wishlist(user_id, title, price, retailer, link, img) VALUES (?, ?, ?, ?, ?, ?);"
                            ,session["user_id"]
                            ,item['title']
                            ,item['price']
                            ,item['retailer']
                            ,item['link']
                            ,item['img']
                        )
                
        except KeyError:
            print('Invalid Data Received')

    except json.decoder.JSONDecodeError:
        print('Invalid Data Received')

    return render_template('results.html')


@app.route("/remove", methods=["POST"])
@login_required
def remove():

    print('in /remove')
    # Gets item to be removed from wishlist
    item = request.get_json()
    try:
        # Check if item is in user's wishlist
        item = item['item']
        row = db.execute("SELECT id FROM users_wishlist WHERE user_id = ? AND link = ?;", session['user_id'], item)

        # If it is remove it
        if len(row) == 1:
            db.execute("DELETE FROM users_wishlist WHERE id = ?;", row[0]['id'])
            print('Success removing')
            
        else:
            print('error finding item in wishlist')

    except KeyError:
        print('key error when removing item from wishlist !')

    return render_template('/wishlist.html')


@app.route("/wishlist", methods=["GET"])
@login_required
def wishlist():

    # Gets all items from user's wishlist
    user_wishlist = db.execute("SELECT * FROM users_wishlist WHERE user_id = ?;", session["user_id"])

    # If user provided their location calculate local currency, else returns prices in USD
    results_details = getLocalCurrency(user_wishlist)

    currency = results_details['currency']
    user_wishlist = results_details['results']

    # Renders wishlist page and passes in the user's wishlist
    return render_template("wishlist.html", user_wishlist=user_wishlist, currency=currency)
    

@app.route('/settings', methods=['GET','POST'])
@login_required
def settings():
    ''' User's settings route'''

    # Base user preference value
    pref = 1
    # Gets user preference (whether user want their history to be recorded or not)
    user_pref = db.execute("SELECT record_history FROM users WHERE id = ?;", session['user_id'])

    # If a record was returned assigned the user's preference value to pref variable
    if len(user_pref) == 1:
        pref = user_pref[0]['record_history']

    # If trying to change passwords
    if request.method == 'POST':
            
            # Get passwords values
            current_pw = request.form.get("currentPassword")
            new_pw = request.form.get("newPassword")

            # If password fields were not filled, warn user
            if not current_pw or not new_pw:
                print("missing pw")
                return render_template("settings.html", alert="Missing Password", pref=pref)
            
            # If no records of the user are found, or current password in db and current_pw do not match, warn user
            row = db.execute("SELECT hash FROM users WHERE id = ?;", session['user_id'])
            if len(row)!= 1 or not check_password_hash(row[0]['hash'], current_pw):
                print("user not found or not same password")
                return render_template("settings.html", alert="User Not Found or Incorrect Current Password", pref=pref)
            
            # Generate new hash and store it in db, alert user that operation was a success
            hash = generate_password_hash(new_pw)
            db.execute("UPDATE users SET hash = ? WHERE id = ?;", hash, session['user_id'])
            print("success")
            return render_template("settings.html", success="Succesfully Changed Password", pref=pref)

    return render_template('settings.html', pref=pref)


@app.route('/deleteHistory', methods=['POST'])
@login_required
def deleteHistory():

    ''' DELETES USER'S HISTORY '''
    db.execute("DELETE FROM users_history WHERE user_id = ?;", session['user_id'])

    return render_template('settings.html')
    

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        # Get values posted by user
        username = request.form.get("username")
        password = request.form.get("password")

        # If password or username is null
        if not password or not username:
            message = "Login Error: Fields Missing"
            return render_template("login.html", message=message)
        
        # Get user's record in database
        user_record = db.execute("SELECT * FROM users WHERE username = ?", username)
        # If returned record is null or greater than 2, redirect user to same page
        if len(user_record) != 1:
            return render_template("login.html", message="Login Error: User Does Not Exist")

        # If password hash in database does not match password posted, redirect user to login page
        if not check_password_hash(user_record[0]["hash"], password):
            return render_template("login.html", message="Login Error: Incorrect Password")
        
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
            return render_template("register.html", message="Register Error: Missing Fields")
        
        # If password does not match confirmation redirect to /register route
        if password != confirmation:
            return render_template("register.html", message="Register Error: Passwords Do Not Match")
        
        # Checks if record with same username already exists, if yes redirect user
        row = db.execute("SELECT * FROM users WHERE username = ?;", username)
        if len(row) > 0:
            return render_template("register.html", message="Register Error: Username Already Exists")
        
        # Generate hash and insert new user into database
        hash_pw = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash, record_history) VALUES (?, ?, 1);", username, hash_pw)

        return redirect("/")
    
    else:
        return render_template("register.html")