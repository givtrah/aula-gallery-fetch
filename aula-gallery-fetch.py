# aula.py
# Author: Ole Hartvig Mortensen, hartvig@gmail.com 
# Based on work by Morten Helmstedt, helmstedt@gmail.com : https://helmstedt.dk/2021/05/aulas-api-en-opdatering/

''' Done: Download all galleries you have access to on aula.dk.
    Todo: Store a simple database of images for later partial download
    and make a list of new images since last download
'''

# Imports
import requests                 # Perform http/https requests
from bs4 import BeautifulSoup   # Parse HTML pages
import json                     # Needed to print JSON API data
import shutil
import os

# User info
user = {
    'username': 'YOUR_AULA_USER_NAME',
    'password': 'YOUR_AULA_PASSWORD'
    }

# basedir

base_dir = "./galleries"


# Start requests session
session = requests.Session()
     
# Get login page
url = 'https://login.aula.dk/auth/login.php?type=unilogin'
response = session.get(url)
 
# Login is handled by a loop where each page is first parsed by BeautifulSoup.
# Then the destination of the form is saved as the next url to post to and all
# inputs are collected with special cases for the username and password input.
# Once the loop reaches the Aula front page the loop is exited. The loop has a
# maximum number of iterations to avoid an infinite loop if something changes
# with the Aula login.
counter = 0
success = False
while success == False and counter < 10:
    try:
        # Parse response using BeautifulSoup
        soup = BeautifulSoup(response.text, "lxml")
        # Get destination of form element (assumes only one)
        url = soup.form['action']   
         
        # If form has a destination, inputs are collected and names and values
        # for posting to form destination are saved to a dictionary called data
        if url:
            # Get all inputs from page
            inputs = soup.find_all('input')
            # Check whether page has inputs
            if inputs:
                # Create empty dictionary 
                data = {}
                # Loop through inputs
                for input in inputs:
                    # Some inputs may have no names or values so a try/except
                    # construction is used.
                    try:
                        # Save username if input is a username field
                        if input['name'] == 'username':
                            data[input['name']] = user['username']
                        # Save password if input is a password field
                        elif input['name'] == 'password':
                            data[input['name']] = user['password']
                        # For all other inputs, save name and value of input
                        else:
                            data[input['name']] = input['value']
                    # If input has no value, an error is caught but needs no handling
                    # since inputs without values do not need to be posted to next
                    # destination.
                    except:
                        pass
            # If there's data in the dictionary, it is submitted to the destination url
            if data:
                response = session.post(url, data=data)
            # If there's no data, just try to post to the destination without data
            else:
                response = session.post(url)
            # If the url of the response is the Aula front page, loop is exited
            if response.url == 'https://www.aula.dk:443/portal/':
                success = True
    # If some error occurs, try to just ignore it
    except:
        pass
    # One is added to counter each time the loop runs independent of outcome
    counter += 1
 
# Login succeeded without an HTTP error code and API requests can begin 

if success == True and response.status_code == 200:
    print("Login success")

    # All API requests go to the below url
    # Each request has a number of parameters, of which method is always included
    # Data is returned in JSON
    
    url = 'https://www.aula.dk/api/v13/'
 
    ### First API request. This request must be run to generate correct correct cookies for subsequent requests. ###
    params = {
        'method': 'profiles.getProfilesByLogin'
        }
    # Perform request, convert to json and print on screen
    response_profile = session.get(url, params=params).json()
#    print(json.dumps(response_profile, indent=4))
     
    ### Second API request. This request must be run to generate correct correct cookies for subsequent requests. ###
    params = {
        'method': 'profiles.getProfileContext',
        'portalrole': 'guardian',   # 'guardian' for parents (or other guardians), 'employee' for employees
    }
    # Perform request, convert to json and print on screen
    response_profile_context = session.get(url, params=params).json()
#    print(json.dumps(response_profile, indent=4))

    # Loop to get institutions and children associated with profile and save
    # them to lists
    institutions = []
    institution_profiles = []
    children = []
    for institution in response_profile_context['data']['institutions']:
        institutions.append(institution['institutionCode'])
        institution_profiles.append(institution['institutionProfileId'])
        for child in institution['children']:
            children.append(child['id'])
     
    children_and_institution_profiles = institution_profiles + children

    ### Gallery
    # seems like the webpage limit for galleries is index = 100 (index 0-100, e.g. 101 galleries - what happend to the rest??!?)
    # use limit 200 for going live, 2 for testing
    params = {
        'method': 'gallery.getAlbums',
        'index': "0",
        'institutionProfileIds[]': children_and_institution_profiles,
        'limit': '200'
        }
    
    response_profile_context = session.get(url, params=params).json()

    # Loop to get all album_ids from the gallery and save
    # them to a list
    album_ids = []
    album_titles = []
    album_dates = []
    for album in response_profile_context['data']:
        album_ids.append(album['id'])
        album_titles.append(album['title'])
        album_dates.append(album['creationDate'])

    del album_ids[0]       # first entry is "your childrens media" - not a real album and most likely your children is tagged wrongly - let's get rid of that
    print("Found " + str(len(album_ids)) + " albums in the gallery - downloading all images")

# Loop through albums based on album_ids collected above

    for album in album_ids:
        params = {
            'method': 'gallery.getMedia',
            'index': "0",
            'institutionProfileIds[]': children_and_institution_profiles,
            'limit': '200',
            'albumId': album
            }   
        
        response_profile_context = session.get(url, params=params).json()

# Loop through images in the album selected above
        
        album_date = response_profile_context['data']['album']['creationDate'][0:10]  

# This part can be improved!
        album_name = response_profile_context['data']['album']['name'].replace(",","_")
        album_name = album_name.replace(" ","_")
        album_name = album_name.replace("/","_")
        album_name = album_name.replace(".","_")
        album_date_name = album_date + "_" + album_name
        
        print("Album date & name: " + album_date_name)

        album_path = os.path.join(base_dir, album_date_name)
        os.makedirs(album_path, exist_ok = True)

        imgcount = 0;
        for images in response_profile_context['data']['results']:
            r = requests.get(images['file']['url'], stream=True)        # get request on full URL
            if r.status_code == 200:
                with open(os.path.join(album_path, images['file']['created'][0:10] + "_" + album_name + "_" + str(imgcount).zfill(2) + "_" + images['file']['name']), 'wb') as f:
                   r.raw.decode_content = True
                   shutil.copyfileobj(r.raw,f)
            imgcount += 1

# Login failed for some unknown reason
else:
    print("Something went wrong when trying to login")


