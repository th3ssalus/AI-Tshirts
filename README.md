If you are interested in print on demand and Etsy side hustles but don't have much spare time, this project is being developed to help you!
Through the use of SmugMug (an image hosting website), printify (a print on demand service), and Etsy (a marketplace developed for small businesses) this project aims to simplify the admin side of 
running a small business online, enabling creative people to spend more time focusing on creating cool things and less time on repetative boring processes.

What does it do?
At the moment this script successfully takes designs from your computer, uploads them to an image hosting website, transfers these images to your printify media library, and generates a t-shirt product with a price of $20
for every design you submit, automatically, and in batch. It also then pushes the final products to the 'draft listings' of your Etsy store, ready to be activated as products!


How does it work?
The Setup
- You create a designated folder to contain designs you have created.
- Using the API service provided by SmugMug, Printify you generate personal keys and tokens for authentication
  enabling you to edit your Printfy and SmugMug libraries through the code.
- Through Etsy's API service you grab your store code, enabling the code to access your store.

The Fun Bit
- You spend your time creating awesome t-shirt designs.
- When you're ready to share them with happy customers you place the image files
  in the designated folder.
- Then you run the script...
- And just like that your Etsy store has as many new T-shirt products as designs you placed in the folder.

Current Pitfalls
- Please be aware: The code at present will not check your folder for designs you have already uploaded.
    - This functionality is being developed.
    - Until then you will have to empty the folder each time you want to create new designs to prevent duplicates.
- SmugMug is a paid service used for image hosting.
    - I am looking at free alternative for image hosting to avoid a payment requirement.
