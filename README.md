# Item Harvest
#### Video Demo:  <URL HERE>
#### Description:
##### Web App Purpose
Via Item Harvest services, users would be able to create an account and browse for items, then add them to and remove them from their wishlist.
This Web App was built using the Flask Framework in Python and Sqlite3 as Database and Backend, with CSS and Bootstrap 5, HTML, Javascript and Jquery for the front-end.

##### Setup
For the web app to work you would need to have:

A .env file containing API keys whose variable names are
OER_API_KEY - Open Exchange Rates API Key
To get currency rates for products'price

EBAY_SB_API_KEY - Ebay API Key
To get items' information when searching for items

OPEN_CAGE_API_KEY - Open Cage API Key
IPIFY_API_KEY - Ipify API Key
To acquire user's country to display items' price in local currency

SECRET_KEY
Used to store user sessions cookies

Then a sqlite3 database named webApp.db which would have tables and fields that follow:

CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, username TEXT NOT NULL, hash TEXT NOT NULL, record_history INTEGER NOT NULL DEFAULT 1);

CREATE TABLE users_wishlist (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, user_id INTEGER NOT NULL, title TEXT NOT NULL, price NUMERIC NOT NULL, retailer TEXT NOT NULL, link TEXT NOT NULL, img TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id));

CREATE TABLE users_history (id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, search TEXT NOT NULL, user_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users(id));

##### Layout of the webpages
All webpages have navbar at the top of the page, credits on the footer and a button to get back at the top of the page, if the user scrolled down.

##### Homepage / Index
This route accepts GET requests.

Via index.html and the controller app.py, the user is presented with a page where they can search for items via Ebay's Finding API and get recommended their previous search results and navigate to other pages with the navbar.

In the homepage, Javascript code in the index.html file would automatically get the IP Address of the user so as to send it to the server and get the user's country so as to know what currency they use.

##### Search Results
This route accepts both GET and POST requests.

For the GET requests, users can search for items and be presented with Ebay's items based on their query. Thereafter the item's title, image, price, retailer (Ebay) would be displayed as well as 3 buttons. One to add items to the user's wishlist, the other to remove them (disabled if item is not already in wishlist and then enabled if it is) and a third one that serves as link to product's actual Ebay link (URL).

In case the user already has some items from the search results in the wishlist, the add button would already be disabled and contain 'Added' as inner HTML, while the remove button would be enabled and allow users to remove existing items from their wishlist directly.

If the country of the user was acquired via the homepage, items would be displayed in the local currency via Open Exchange Rates API to get the current value of items in relation to USD. If no country was acquired the base case of items' prices would be in USD.

The POST requests would be used to sort the items from the search results in ascending or descending order of price, based on the user's choice if they did not choose whether the method to sort in, the base case is ascending.

##### Wishlist / My Harvest
This route accepts GET requests.

In this route, the user will be presented with their wishlist items, as well the total cost on top the page below the navbar.
Users can see the items as they would in search results with title, price, image, link : And items at local prices if a country was assigned to the user via sessions

Users would be to remove items without reloads similar to the search results route via AJAX requests, which would consequently update the total at the top of the page. In order to avoid floating point imprecision, the Javascript in the wishlist.html uses a library called BigDecimal that would perform accurate floating values calculations.

##### Settings
This route accepts both GET and POST requests.

In this route, using GET, users would be able to delete their search history from the database, so that their search recommendations on index route would be empty. Moreover they would be able to disable/enable the recording of their search queries by the Controller (app.py) and database if they wish to.

Using the POST requests, users would be able to change their passwords if they need to by entering their current password and new password, and be alerted whether fields were missing, their current password does not match with the password entered or whether the operation was a success.

##### Login
This route accepts both GET and POST requests.

In this route users can log into their account if they already have one, and be alerted if the password is incorrect or the if the user does not exist or if fields are missing.

If users try to access other routes (except Register) and are not logged in, they would be redirecteedd to this route.

##### Register
This route accepts both GET and POST requests.

In this route users would be able to create an account on Item Harvest and be alerted in case the username is already taken, or passwords do not match, or fields are missing.

##### Additional Routes
These routes use mainly POST as method.

Direct Add would add items to the user's wishlist and Remove route would remove items from the user's wishlist

Logout would clear the user's current session (Uses GET)

Enable DisableHistory route would update the database records of the user to change whether they want their history to be recorded or not.

Delete History would delete all records of the search queries of the user in the database.

##### helpers.py
This file would be used to declare and implement functions.

The function formatPrice would be used as a jinja filter to format prices in the search results and wishlist routes, to 2 decimal places.

getLocalCurrency would get the local currency of the user based on their country and calculate the price of the products in their local currency via the Open Exchange Rate API and return the list of items of the search results in the local prices.

EbayFind would take a search query, make a request to Ebay's Finding API in order to get items and return a list of dictionaries with all of their details such as price, image, link, title and more.

login_required would be used as a decorator to routes such as index, searchResults, wishlist and so on, to prevent users from accessing these routes without logging in.

getCountryByIP would take in the IP Address of the user and make a request to IPIFY's API in order to return the country of the user.

refreshExchangeRates would be used to start a background task via APScheduler's library to make calls to OpenExchange Rates API and cache in the new rates and update the json containing these rates at 8AM and 8PM Mauritian Time as long as the server is running.

##### Additional files
style.css contains some classes used for the elements used in HTML.
There also background images used in the layout.html, as well as the Github icon that redirects to my Github account Matthieu-MG.

Additional icon such as the up arrow which is used as a button to get at the top of the page.

The database of this Web App itself that stores information about the users, their wishlist, and their search history.

data.json is a file (not pushed to repo) that is used to cache in the current exchange rates.

.env (not pushed to repo) stores environment variables such as API keys and secret keys for sessions 