# Import Necessary Libraries
import requests #enables API requests using json payloads.
import requests_oauthlib #enables Online Authentication for interacting with the SmugMug API.
import json #for ease of use as this script works a lot with json file format.
import re #regular expressions are used throughout the script for checking filenames, etc.
import hashlib
import os
from time import sleep #used to create delays in the script as slow internet or large packets can cause time conflicts as the code runs.

design_folder = "" #a file path (as a string) for the folder where product designs are placed.
album_uri = "" #the 'api URI' for the SmugMug photo album, e.g. '/api/v2/album/MGS57'.
shop_id = "" #id (as a string) for the etsy store being used, e.g. 5754747
printify_key = "" #user's private printify key (as a string), generated from their account through printify's api service.
printify_auth = {'Authorization': f'Bearer {printify_key}'} #json format authentication payload, this accompanies pull and push requests to the printify API to authenticate requests.

# Defining your OAuth 1.0a credentials to use SmugMug image hosting
## User's will need an active account to SmugMug.com, alternatively images can be hosted on github
## and raw image urls can be sent to printify, in this case the following code is not necessary...

# ------------------------------------- SMUGMUG IMAGE HOSTING CODE -------------------------------------------------------------------------
consumer_key = "" #consumer key can be generated on the SmugMug website using their API service.
consumer_secret = "" #consumer secret can be generated on the SmugMug website using their API service.
request_token_url = "https://secure.smugmug.com/services/oauth/1.0a/getRequestToken" #this is the SmugMug request token URL used for OAuth
access_token_url = "https://secure.smugmug.com/services/oauth/1.0a/getAccessToken" #this is the SmugMug Access token URL used for OAuth
authorize_url = "https://secure.smugmug.com/services/oauth/1.0a/authorize" #this is the SmugMug authorize url used for OAuth
callback_url = 'oob' #this is the SmugMug callback URL used for OAuth

# Create an OAuth 1.0a session with HMAC-SHA1 signature method and your credentials
oauth = requests_oauthlib.OAuth1Session(
    client_key=consumer_key,
    client_secret=consumer_secret,
    callback_uri=callback_url,
    signature_method="HMAC-SHA1"
)

# Fetch the request token and authorize URL
fetch_response = oauth.fetch_request_token(request_token_url, json={"oauth_callback": 'oob'})
authorize_url = oauth.authorization_url(authorize_url)

# Print the authorize URL and prompt the user to authorize the app
print("Authorize URL: ", authorize_url)
auth_code = input("Enter authorization code: ")

# Fetch the access token using the request token and verifier
token_response = oauth.fetch_access_token(access_token_url, verifier=auth_code)
print(token_response)

#SMUGMUG Functions
def smugmug_upload_image(image_path, image_type='image/png'):
    """Upload image to specified Album URI (NOT Album node URI), given an authenticated session and image file path."""
    with open(image_path, 'rb') as image:
        image_data = image.read()
    for i in range(2):
        # Retry once. Switching between SmugMug API and Uploader API occasionally causes SmugMug to RST connection.
        try:
            r = oauth.post(
                'https://upload.smugmug.com/',
                headers={
                    'Accept': b'application/json',
                    'Content-Length': str(len(image_data)),
                    'Content-MD5': hashlib.md5(image_data).hexdigest(),
                    'Content-Type': image_type,
                    'X-Smug-AlbumUri': album_uri,
                    'X-Smug-FileName': os.path.basename(image_path),
                    'X-Smug-ResponseType': 'JSON',
                    'X-Smug-Version': 'v2',
                },
                data=image_data,
            )
        except requests.exceptions.ConnectionError as e:
            r = False
            print(f'[WARN] Upload attempted while offline (attempt {i+1}). "{e}".')
        else:
            break
    if r and r.json()['stat'] == 'ok':
        print(f"[INFO] Upload Success: {r.json()['Image']['URL']}")
    else:
        print(f'[WARN] Upload Failed: "{image_path}"')   # TODO: increase failure handling. Upload error codes aren't great.
    return r

def grab_imageurls(images):
    '''If you pass grab_mockups() it will grab mockup urls, if you pass grab_designs() it will grab design urls.'''
    urls = {}
    ponyo_url = 'https://www.smugmug.com/api/v2/album/MPPz6M!images'
    album_data = oauth.get(ponyo_url,headers={'Accept':'application/json'})
    
    if album_data.status_code == 200:
        #go through album and designs folder and grab matching image based on name
        for image in images:        
            #iterate through the number of images we have in our album
            for x in range(len(album_data.json()['Response']['AlbumImage'])):
                #if an image with the same filename is found in the smugmug album
                if image == album_data.json()['Response']['AlbumImage'][x]['FileName']:
                    #create an API endpoint link for the high resolution version of that image
                    link = album_data.json()['Response']['AlbumImage'][x]['Uris']['LargestImage']['Uri']
                    #get the information from that endpoint
                    b = oauth.get(f'https://www.smugmug.com{link}',headers={'Accept':'application/json'})
                    #append the dictionary "design_urls" to include that design with an associated image link
                    # to be uploaded to printify
                    urls[image] = b.json()['Response']['LargestImage']['Url']

        return urls
    else: 
        print('Something went wrong with the Image URLs')
        
# ------------------------------------------------- END -------------------------------------------------------------------------------------------------
        
# PRINTIFY FUNCTIONS
def grab_images(folder):
    '''scans the design folder and will grab the image name for every file in the folder'''
    images = []
    files = os.listdir(folder) #design folder here
    for file in files:
        images.append(file)
    return images

def printify_upload_image(image_name,image_url): #needs editing for file type flexibility
    ''' Takes the name and URL of an image and uses this information alongside a predefined
    authentication json payload to push an upload request to the user's printify account media library for later use.
    '''
    upload_url = "https://api.printify.com/v1/uploads/images.json"
    payload = {"file_name": f"{image_name}.png", "url": image_url}
    r = requests.post(upload_url, headers=printify_auth, json=payload)
    print(f'Printify Image Upload Status: {r.status_code}')

def image_grab(image_name):
    ''' Grab the correct image from the printify media library based on the
        design name present in the designs folder on user's computer.
    '''
    url = "https://api.printify.com/v1/uploads.json"
    r = requests.get(url, headers=printify_auth)
    images = r.json()['data']
    for image in images:
        pattern = re.compile(f'^{image_name}')
        if pattern.match(image['file_name']):
            return image['id']

def identify_variants(print_provider):
    ''' Identify variants provided by chosen print provider,
        variants are different options based on size and colour,
        e.g. variant 1 = [Product: T-shirt, Size: XS, Colour: Red, Price: $22]
    '''
    url = f"https://api.printify.com/v1/catalog/blueprints/12/print_providers/{print_provider}/variants.json"
    r = requests.get(url, headers=printify_auth)
    print(f'Indentifying Variants Status: {r.status_code} \n') 
    return(r.json())
    
def colour_metadata(provider,price): 
    ''' Identifies the available colours from the chosen print provider
        and their price, then returns this information in a json format
        to be used in a post request when creating the product.
    '''
    tshirts = []
    metadata = {}
    variants = identify_variants(provider)['variants']
    
    for variant in variants:
        metadata.update({'id':variant['id'],'price':price,'is_enabled':True})
        tshirts.append(metadata)
        metadata={}
    return(tshirts)
    
def variants(variants):
    ''' Returns a list of the IDs of each variant collected by colour_metadata().
        This is generated as for the product post request to the printify API,
        we require an array of variant IDs as one of the values in the request.
    '''
    variant_ids = []
    for variant in variants:
        variant_ids.append(variant['id'])
    return variant_ids


# ---------------------------------------------------------------------------------------------------------------------------------
### What does this greyed out code do?
# This code checks the filename of mockups stored on the user's computer for variant keywords.
# This script is designed to work with bella and canvas 3001 t-shirt colourways and so scans the mockup images
# for the colours and returns a list of the colours we already have mockups for, identifying which variants lack
# storefront product images. This can be used to identify gaps in the user experience as ideally each colourway offered
# would also have a reference image on the storefront.

# def variantsxmockups(variant_info,mockup_names,variant_ids):
#     '''Concatenates the colourway with the corresponding variant IDs for matching IDs to our created mockups'''
#     variants = []
#     color_ids = []
#     output = {}
#     current_color = ''
    
#     for x in range(len(variant_info)):
#         for mockup in mockup_names:
#             color = variant_info[x]['options']['color']
#             id = variant_info[x]['id']
#             try:
#                 if color == mockup.split('3001-')[1].split('.')[0]:
#                     variants.append(f'{color}-{id}')
#             except:
#                 print('Error: Rename mockups!')
                
#     variants = sorted(variants)
#     current_color = variants[0].split('-')[0]
    
#     for variant in variants:
#         y = variant.split('-')
        
#         if y[0] == current_color:
#             color_ids.append(y[1])
#         else:
#             output[current_color]=color_ids
#             color_ids = []
#         current_color = y[0]
#     #this is needed because the last colour won't have a chance in the logic to have it's varaints added to the dictionary
#     #once the final color id is added to the list it exits the loop before having a chance to run the else statement
#     output[current_color]=color_ids
        
#     return output        
# ------------------------------------------------------------------------------------------------------------------------------------

def create_tshirt(listing_title,provider,image_id,price): #variants should be a list of dictionaries
    ''' Create a t-shirt product on the user's printify account. Takes the title of the product, the print provider's unique ID,
        the ID of the design image that should be selected from the user's printify media library, and the price that should be set
        for the product and generates a finished product on the user's account.
    '''
    #required libraries and authentication key    
    metadata = colour_metadata(provider,price)#calling my metadata generator
    
    #posting a listing
    url = f"https://api.printify.com/v1/shops/{shop_id}/products.json"
    payload = {
        "title": listing_title,
        "description": "Great product",
        "blueprint_id": 12, #bella+canvas t-shirt
        "print_provider_id": provider,
        "variants": metadata,
        "print_areas":
        [
            {
              "variant_ids": variants(metadata), #what does this do? - variants used in mockup images, mockups can be uploaded via url
              "placeholders": [
                {
                  "position": "front",
                  "images": [
                      {
                        "id": image_id, 
                        "x": 0.5, 
                        "y": 0.5, 
                        "scale": 1,
                        "angle": 0
                      }
                  ]
                }
              ]
            }
          ]
    }
    r = requests.post(url, headers=printify_auth, json=payload)
    print(f'HTTP Posting a listing: {r.status_code}')
    return(r.json()['id'])

def publish_product(shop_id,products_ids):
    '''Use with care! This will charge you $0.20 with each listing posted.
        Takes the Etsy shop id defined earlier and the ids of printify products created by
        the script and pushes them to the Etsy store in drafts. These can then be activated
        from the storefront as products.'''
    data = {
    "title": True,
    "description": True,
    "images": True,
    "variants": True,
    "tags": True,
    "keyFeatures": True,
    "shipping_template": True
    }
    for product in product_ids:  
        url = f"https://api.printify.com/v1/shops/{shop_id}/products/{product}/publish.json"
        pub = requests.post(url,headers=printify_auth,json=data)
        print(f'Product Upload Status: {pub.status_code}')


# MAIN
designs = grab_images(design_folder) # grab the filenames of each design file currently in the design folder
# mockups = grab_images(mockup_folder) - not needed as cannot change mockups on printify currently...
old_design_urls = grab_imageurls(designs) # grab the urls for each design image from SmugMug gallery
# mockup_urls = grab_imageurls(mockups) - not needed as cannot change mockups on printify currently...
metadata = colour_metadata(27,2000) # define metadata for the product, 27 = p
products = [] # define a product array that will be populated with every design created and to show the user what products were created.

#variantsxmockups(identify_variants(27)['variants'],mockups,variants(metadata)) - not needed as cannot change mockups on printify currently...
 
#SMUGMUG UPLOAD FROM DIRECTORY
#Upload designs
for design in designs:
    image_path = f'{design_folder}/{image}'
    smugmug_upload_image(image_path)
    
#Upload mockups - not needed as cannot change mockups on printify currently...
# for mockup in mockups:
#     image_path = f'{mockup_folder}/{image}'
#     smugmug_upload_image(image_path)

#Wait for the Upload to be refreshed
sleep(60)

new_design_urls = grab_imageurls(designs)
# need a difference checker here to avoid recreating old products
# i.e. new_design_urls = new_design_urls - old_design_urls

# ------------------------------------------------------------------------------------
# What does this greyed out code do? - Uploads each mockup image to printify media library
## WORKS, BUT CURRENTLY THE SCRIPT CANNOT CHANGE MOCKUPS ON PRINTIFY, THIS MUST BE DONE ON
## THE ETSY STOREFRONT.

### CODE:
# for url in mockup_urls.keys():
#     upload_image(url, mockup_urls[url])

# -------------------------------------------------------------------------------------
    
#create t-shirt for each design while collecting and collating the response information.
for design in designs.keys():
    #upload design to user's printify media library from SmugMug url.
    printify_upload_image(design, designs[design])
    #create t-shirt using design and metadata.
    products.append(create_tshirt(design.split('.')[0], 27, image_grab(design), 2000)) #create a product and track which products are created.

print(f'Here are the finished products: {products}')


# At this point t-shirts have been created with every design in the design folder,
# the filename of each design image has been used to generate the title of each design.


# NOW WE CAN PUSH THEM TO OUR ETSY STORE - BE WEARY, ONCE CONNECTED
# TO AN ETSY STORE, EACH NEW LISTING INCURS A $.20 LISTING FEE!!!!
#POST /v1/shops/{shop_id}/products/{product_id}/publish.json
publish_product(shop_id,product_ids)


