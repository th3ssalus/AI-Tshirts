# SETUP
import requests
import requests_oauthlib
import json
import re
import hashlib
import os
from time import sleep

design_folder = 'C:/Users/Harry/Desktop/test folder'
mockup_folder = 'C:/Users/Harry/Desktop/mockups'
album_uri = '/api/v2/album/MPPz6M' #this is the Ponyo album
shop_id = '5764748'

printify_key = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIzN2Q0YmQzMDM1ZmUxMWU5YTgwM2FiN2VlYjNjY2M5NyIsImp0aSI6ImIxMzI4YjkzYWMwZWI0MjgwYTFlYmE5NmNjNTRlYzI0NWFjMGZkNWU2NjIyNmY1N2RmYTM3ZmFjODJjNzA4NDI3YzgwMjE0OWU0ZmNiODEwIiwiaWF0IjoxNjgyNTI5MjIwLjQ5MjIyNiwibmJmIjoxNjgyNTI5MjIwLjQ5MjIzLCJleHAiOjE3MTQxNTE2MjAuNDg3MzMsInN1YiI6IjEwNzMxODEyIiwic2NvcGVzIjpbInNob3BzLm1hbmFnZSIsInNob3BzLnJlYWQiLCJjYXRhbG9nLnJlYWQiLCJvcmRlcnMucmVhZCIsIm9yZGVycy53cml0ZSIsInByb2R1Y3RzLnJlYWQiLCJwcm9kdWN0cy53cml0ZSIsIndlYmhvb2tzLnJlYWQiLCJ3ZWJob29rcy53cml0ZSIsInVwbG9hZHMucmVhZCIsInVwbG9hZHMud3JpdGUiLCJwcmludF9wcm92aWRlcnMucmVhZCJdfQ.AKDbk1W2B4gaYqjQDaA0l147RaDGbuXObotRMAdyArYy20G9zcn5oI9_X5UwBOQ6WFHMoGnoPG7KwKZvi7E'

printify_auth = {'Authorization': f'Bearer {printify_key}'}

# Define your OAuth 1.0a credentials
consumer_key = 'qXPB8BF2Z5pVxpTsHSjk6tj558hpnSs8'
consumer_secret = '697VPzwdGp4FQ2CxxBMVkW5JpHQn53qhfcnnXMhrwKkgdRqTLLQFzDsBNmXrnp8P'
request_token_url = "https://secure.smugmug.com/services/oauth/1.0a/getRequestToken"
access_token_url = "https://secure.smugmug.com/services/oauth/1.0a/getAccessToken"
authorize_url = "https://secure.smugmug.com/services/oauth/1.0a/authorize"
callback_url = 'oob'

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

# FUNCTIONS

def grab_images(folder):
    '''takes either the design or mockup folder and will grab the image name for every file in the folder'''
    images = []
    files = os.listdir(folder) #design folder here
    for file in files:
        images.append(file)
    return images

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
    '''If you pass grab_mockups() it will grab mockup urls, if you pass grab_designs() it will grab design urls'''
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
    
def printify_upload_image(image_name,image_url): #needs editing for file type flexibility
    upload_url = "https://api.printify.com/v1/uploads/images.json"
    payload = {"file_name": f"{image_name}.png", "url": image_url}
    r = requests.post(upload_url, headers=printify_auth, json=payload)
    print(f'Printify Image Upload Status: {r.status_code}')

def image_grab(image_name):
    url = "https://api.printify.com/v1/uploads.json"
    r = requests.get(url, headers=printify_auth)
    images = r.json()['data']
    for image in images:
        pattern = re.compile(f'^{image_name}')
        if pattern.match(image['file_name']):
            return image['id']

def identify_variants(print_provider):
    url = f"https://api.printify.com/v1/catalog/blueprints/12/print_providers/{print_provider}/variants.json"
    r = requests.get(url, headers=printify_auth)
    print(f'Indentifying Variants Status: {r.status_code} \n') 
    return(r.json())
    
def colour_metadata(provider,price): 
    tshirts = []
    metadata = {}
    variants = identify_variants(provider)['variants']
    
    for variant in variants:
        metadata.update({'id':variant['id'],'price':price,'is_enabled':True})
        tshirts.append(metadata)
        metadata={}
    return(tshirts)
    
def variants(variants):
    variant_ids = []
    for variant in variants:
        variant_ids.append(variant['id'])
    return variant_ids
    
def variantsxmockups(variant_info,mockup_names,variant_ids):
    '''Concatenates the colourway with the corresponding variant IDs for matching IDs to our created mockups'''
    variants = []
    color_ids = []
    output = {}
    current_color = ''
    
    for x in range(len(variant_info)):
        for mockup in mockup_names:
            color = variant_info[x]['options']['color']
            id = variant_info[x]['id']
            try:
                if color == mockup.split('3001-')[1].split('.')[0]:
                    variants.append(f'{color}-{id}')
            except:
                print('Error: Rename mockups!')
                
    variants = sorted(variants)
    current_color = variants[0].split('-')[0]
    
    for variant in variants:
        y = variant.split('-')
        
        if y[0] == current_color:
            color_ids.append(y[1])
        else:
            output[current_color]=color_ids
            color_ids = []
        current_color = y[0]
    #this is needed because the last colour won't have a chance in the logic to have it's varaints added to the dictionary
    #once the final color id is added to the list it exits the loop before having a chance to run the else statement
    output[current_color]=color_ids
        
    return output        
    
def create_tshirt(listing_title,provider,image_id,price): #variants should be a list of dictionaries
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


# MAIN
designs = grab_images(design_folder)
mockups = grab_images(mockup_folder)
design_urls = grab_imageurls(designs)
mockup_urls = grab_imageurls(mockups)
metadata = colour_metadata(27,2000)
products = []
#variantsxmockups(identify_variants(27)['variants'],mockups,variants(metadata))
 
#SMUGMUG UPLOAD FROM DIRECTORY
#Upload designs
for design in designs:
    image_path = f'{design_folder}/{image}'
    smugmug_upload_image(image_path)
#Upload mockups
for mockup in mockups:
    image_path = f'{mockup_folder}/{image}'
    smugmug_upload_image(image_path)
#Wait for the Upload to be refreshed
sleep(60)
    
#PRINTIFY URL UPLOAD
#upload each mockup image to printify media library
for url in mockup_urls.keys():
    upload_image(url, mockup_urls[url])
    
#create t-shirt for each while keeping the response information
for design in designs.keys():
    #upload design to printify from SmugMug url
    upload_image(design, designs[design])
    #create t-shirt using design
    products.append(create_tshirt(design.split('.')[0], 27, image_grab(design), 2000))

print(f'Here are the finished products: {products}')