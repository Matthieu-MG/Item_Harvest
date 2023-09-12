# Item Harvest
#### Video Demo:  <URL HERE>
#### Description:
##### Web App Purpose
Via Item Harvest services, users would be able to create an account and browse for items, then add them to and remove them from their wishlist.
This Web App was built using the Flask Framework in Python and Sqlite3 as Database and Backend, with CSS and Bootstrap 5, HTML, Javascript and Jquery for the front-end.

##### Layout of the webpages
All webpages have navbar at the top of the page, credits on the footer and a button to get back at the top of the page, if the user scrolled down.

##### Homepage / Index
This route accepts GET requests

Via index.html and the controller app.py, the user is presented with a page where they can search for items via Ebay's Finding API and get recommended their previous search results and navigate to other pages with the navbar.

In the homepage, Javascript code in the index.html file would automatically get the IP Address of the user so as to send it to the server and get the user's country so as to know what currency they use.

###### Search Results
This route accepts both GET and POST requests.

For the GET requests, users can search for items and be presented with Ebay's items based on their query. Thereafter the item's title, image, price, retailer (Ebay) would be displayed as well as 3 buttons. One to add items to the user's wishlist, the other to remove them (disabled if item is not already in wishlist and then enabled if it is) and a third one that serves as link to product's actual Ebay link (URL).

In case the user already has some items from the search results in the wishlist, the add button would already be disabled and contain 'Added' as inner HTML, while the remove button would be enabled and allow users to remove existing items from their wishlist directly.

If the country of the user was acquired via the homepage, items would be displayed in the local currency via Open Exchange Rates API to get the current value of items in relation to USD. If no country was acquired the base case of items' prices would be in USD.

The POST requests would be used to sort the items from the search results in ascending or descending order of price, based on the user's choice if they did not choose whether the method to sort in, the base case is ascending.

##### Wishlist / My Harvest
This route accepts GET requests

In this route, the user will be presented with their wishlist items, as well the total cost on top the page below the navbar.
Users can see the items as they would in search results with title, price, image, link : And items at local prices if a country was assigned to the user via sessions

Users would be to remove items without reloads similar to the search results route via AJAX requests, which would consequently update the total at the top of the page. In order to avoid floating point imprecision, the Javascript in the wishlist.html uses a library called BigDecimal that would perform accurate floating values calculations.

##### Settings
This route accepts both GET and POST requests

In this route, using GET, users would be able to delete their search history from the database, so that their search recommendations on index route would be empty. Moreover they would be able to disable/enable the recording of their search queries by the Controller (app.py) and database if they wish to.

Using the POST requests, users would be able to change their passwords if they need to by entering their current password and new password, and be alerted whether fields were missing, their current password does not match with the password entered or whether the operation was a success.