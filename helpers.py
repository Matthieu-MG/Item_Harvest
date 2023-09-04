from flask import session, redirect
import requests
import json
import os
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def getCurrency(country):

    if not os.path.isfile('data.json'):

        # Gets current currency values via the open exchange rates api
        parameters = {"app_id": os.getenv("OER_API_KEY")}
        response = requests.get('https://openexchangerates.org/api/latest.json', params=parameters)
        data = response.json()
        with open('data.json', 'w') as file:
            json.dump(data, file)

    else:
        with open('data.json', 'r') as file:
            data = json.load(file)

    response = requests.get(f'https://restcountries.com/v3.1/name/{country}/')
    if response.status_code == 200:
        country_details = response.json()
        currency = list(country_details[0]['currencies'].keys())[0]
        rate = data['rates'][currency]
        return {
            "currency" : currency,
            "rate" : rate
        }
        
    return None

def getCountry(longitude, latitude):

    # Get Open Cage's API Key and make request
    api_key = os.getenv("OPEN_CAGE_API_KEY")
    response = requests.get(f"https://api.opencagedata.com/geocode/v1/json?q={latitude}+{longitude}&key={api_key}&pretty=1")
    try:
        # If response code is ok
        if response.status_code == 200:
            # Converts JSON data to Dictionary
            country = response.json()
            try:
                # Get country and return it
                country = country['results'][0]['components']['country']
                return country

            # In case of invalid data or no country was found, handles exception
            except KeyError:
                print("Invalid Key")

    # In case could not connect to Open Cage's API, handles exception
    except ConnectionError:
        print("Could not connect to API")

    return None


def getLocalCurrency(items):

    # Currency to be displayed in webpage
    currency = "USD"
    try:
        # If user allowed for their location to be known, calculate local price for each products
        if session['user_country']:
            user_currency = getCurrency(session['user_country'])
            currency = user_currency['currency']
            rate = user_currency['rate']
            
            for item in items:
                item['local_price'] = float(item['price']) * rate

    except KeyError:
        print("Does not have a country assigned")

    return{
        'currency': currency,
        'results': items
    }

def formatPrice(value):
    return f"{value:.2f}"

def EbayFind(query):

    # Gets API KEY
    app_id = os.getenv("EBAY_SB_API_KEY")

    try:
        # Makes API Request to EBAY
        response = requests.get(f"https://svcs.ebay.com/services/search/FindingService/v1?OPERATION-NAME=findItemsAdvanced" \
                f"&SERVICE-VERSION=1.0.0" \
                f"&SECURITY-APPNAME={app_id}" \
                f"&RESPONSE-DATA-FORMAT=JSON" \
                f"&REST-PAYLOAD" \
                f"&keywords={query}")
        
        # IF Status Code is done
        if response.status_code == 200:
            
            # Convert To JSON and stores search results as a list in data
            data = response.json()

            try:
                data = data['findItemsAdvancedResponse'][0]['searchResult'][0]
                #print(data['@count'])

                # If request returned at least one item
                if len(data) > 1 :

                    # Will store a dictionary (containing name, price, etc...) for each item
                    results = []

                    # Iterates through each item of the search results
                    for item in (data['item']):

                        # Gets the item's information
                        itemId = item['itemId'][0]
                        title  = item['title'][0]
                        image = item['galleryURL'][0]
                        item_URL = item['viewItemURL'][0]

                        sellingStatus = item['sellingStatus'][0]
                        state = sellingStatus['sellingState'][0]
                        pricing = sellingStatus['currentPrice']
                        currency = pricing[0]['@currencyId']
                        price = pricing[0]['__value__']

                        # Stores it in a dictionary
                        item_info = {
                            "title" : title,
                            "id" : itemId,
                            "image" : image,
                            "link" : item_URL,
                            "state" : state,
                            "currency" : currency,
                            "price" : price,
                            "retailer" : 'ebay'
                        }
                        # Add that dictionary to the list
                        results.append(item_info)
                    
                    # Return the list (of dictionaries) of search results
                    return results
                
                # If searchResults is 0, returns empty list
                else:
                    return []
            
            # Handles case where trying to access a key that does not exist such as searchResult
            except KeyError:
                return [] 
            
        # If status code is not 200 returns an empty list
        return []
    
    # Handles case where could not connect to API
    except ConnectionError:
        return []


def EtsyFind():
    app_id = os.getenv('ETSY_API_KEY')
    response = requests.get(f'https://openapi.etsy.com/v3/application/shops/{app_id}/listings/active/')

    if response.status_code == 200:
        print(response.json())

    else:
        print(response)
        print('not ok')