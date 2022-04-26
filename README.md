# aula-gallery-fetch
A python script to fetch all media from galleries you have access to from aula.dk, a Danish learning management system

Reason this script exists: Downloading the whole gallery using the aula.dk website usually crashes the api resulting in no download. Furthermore, the downloaded files are not sorted by gallery album, nor is the media creation date available when downloaded through the website.

# How to use
Download script (git clone). 
Install needed python modules (requests, BeautifulSoup, json, shutil, os)
Edit script to add your username and password (you CANNOT use NemID/MitID, you have to make a Unilogin on the aula.dk website). 

Then just run the script using python.
