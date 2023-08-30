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


def EbayFind(query):

    # Gets API KEY
    app_id = os.getenv("EBAY_SB_API_KEY")

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
                image = item['galleryURL']
                item_URL = item['viewItemURL'][0]

                sellingStatus = item['sellingStatus'][0]
                state = sellingStatus['sellingState'][0]
                pricing = sellingStatus['currentPrice']
                currency = pricing[0]['@currencyId']
                price = pricing[0]['__value__']

                # Stores it in a dictionary
                item_info = {
                    'title' : title,
                    'id' : itemId,
                    'image' : image,
                    'link' : item_URL,
                    'state' : state,
                    'currency' : currency,
                    'price' : price,
                    'retailer' : 'ebay'
                }
                # Add that dictionary to the list
                results.append(item_info)
            
            # Return the list (of dictionaries) of search results
            return results
        
    # Else return an empty list
    return []

def EbayFindByID(productId):
    
        # Gets API KEY
    app_id = os.getenv("EBAY_SB_API_KEY")

    # Makes API Request to EBAY
    response = requests.get(f"https://svcs.ebay.com/services/search/FindingService/v1"\
             f"?OPERATION-NAME=findItemsByProduct" \
             f"&SERVICE-VERSION=1.0.0" \
             f"&SECURITY-APPNAME={app_id}" \
             f"&RESPONSE-DATA-FORMAT=JSON" \
             f"&REST-PAYLOAD" \
             f"paginationInput.entriesPerPage=2"\
             f"&productId.@type=ReferenceID"\
             f"&productId={productId}")
    
    if response.status_code == 200:
        data = response.json()
        data = data['findItemsByProductResponse'][0]['searchResult'][0]
        
        if data['@count'] == '0':
            return
        
        results = data['item']
        if len(results) > 1:
            for result in results:
                print(result['itemId'][0])

    print('finished')
    return None

def FindProduct():
    response = requests.get('https://open.api.ebay.com/shopping?'\
    'callname=FindProducts'\
    '&responseencoding=JSON'\
    '&siteid=0'\
    '&version=967'\
    '&QueryKeywords=harry%20potter'\
    '&AvailableItemsOnly=true'\
    '&MaxEntries=2')
    if response.status_code == 200:
        print(response.json())
    
    else:
        print('failure')