from flask import Flask, render_template, request, redirect, session
from helpers import login_required

app = Flask("__name__")

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

        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            return redirect("/register")
        

        return redirect("/")
    
    else:
        return render_template("register.html")