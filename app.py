from flask import Flask, render_template, request, redirect, session

app = Flask("__name__")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/searchResults", methods=["GET", "POST"])
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