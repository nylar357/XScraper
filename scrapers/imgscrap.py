import requests                                                                                                                                                                             
import os                                                                                                                                                                                   
from bs4 import BeautifulSoup                   
from urllib.parse import urljoin, urlparse      
# --- Creation ---
# by nylar357
# email :bryce_polymorph@proton.me
# www.linkedin.com/in/brycezg
# Free Use but please give me some credit

# --- Configuration ---                                                                                                     
# images scraper - prompt supported #                                                                                                                                                
def scrape_images(url, folder_name="downloaded_images"):                                                                                        
    """                                                                                                                                         
    Scrapes all images from a given URL and saves them to a specified folder.                                                                   
                                                                                                                                                
    Args:                                                                                                                                                                  
        url (str): The URL of the website to scrape.                                                                                            
        folder_name (str): The name of the folder to save images in.                                                                            
                           Defaults to 'downloaded_images'.                                                                                                                
    """                                                                                                                                         
    print(f"Attempting to scrape images from: {url}")                                                                                           
                                                                                                                                                
    # --- 1. Create folder if it doesn't exist ---                                                                                                                                          
    if not os.path.exists(folder_name):                                                                                                                                    
        try:                                                                                                                                                               
            os.makedirs(folder_name)               
            print(f"Created directory: {folder_name}")
        except OSError as e:                                                                                                                                                                
            print(f"Error creating directory {folder_name}: {e}")
            return # Stop if directory creation fails                                                                
                                                                                              
    # --- 2. Send HTTP Request ---                           
    headers = {                                                                           
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'                                                                                                
    } # Mimic a browser to avoid potential blocking                                           
    try:                                        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)                           
        print("Successfully fetched the webpage.")                                                                   
    except requests.exceptions.RequestException as e:                                                                                                                                       
        print(f"Error fetching URL {url}: {e}")                                                                      
        return                                                                                                       
                                                                                                                     
    # --- 3. Parse HTML ---                                                                                                                                                                 
    soup = BeautifulSoup(response.content, 'html.parser')                  
                                                                                                                                                             
    # --- 4. Find all image tags ---                                                                                 
    img_tags = soup.find_all('img')                                                                                                                          
    print(f"Found {len(img_tags)} image tags.")                                                                                                              
                                                                                                                                                             
    if not img_tags:                                                                                                                                         
        print("No image tags found on the page.")                                                                                                            
        return                                                                                                                                               
                                                                                                                                                             
    # --- 5. Download images ---                                                                                                                             
    downloaded_count = 0                                                                                                                                     
    for img_tag in img_tags:     
        img_url = img_tag.get('src')                                                                                                                         
        if not img_url:                                  
            # Sometimes the actual source is in 'data-src' or other attributes                                                                               
            img_url = img_tag.get('data-src')                                                                                                                
            if not img_url:                                                                                                                                  
                # print("Skipping tag with no 'src' or 'data-src'.")                                                                                         
                continue # Skip if no src found                                                                                                              

        # Make the URL absolute (handle relative URLs like /images/logo.png)                                         
        img_url = urljoin(url, img_url)                                                    

        # Basic check if it looks like an image URL (optional but good)
        # You might want to refine this check based on expected image types
        if not any(img_url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg']):                                                                                                                           
             # Skip data URIs or potentially non-image links
             if img_url.startswith('data:image'):         
                 print(f"Skipping data URI image.")             
             else:
                print(f"Skipping potentially non-image URL: {img_url[:80]}...") # Print start of URL                                                                                                                                       
             continue

        try:   
            # Get the image content                                                                                  
            img_response = requests.get(img_url, stream=True, headers=headers, timeout=10)
            img_response.raise_for_status()
                                                                                              
            # Extract filename from URL      
            parsed_url = urlparse(img_url)      
            # Use os.path.basename on the path part of the URL                                                                                                                              
            # Handle cases where path might be empty or just '/'                                                     
            img_filename = os.path.basename(parsed_url.path) if parsed_url.path and parsed_url.path != '/' else f"image_{downloaded_count+1}.jpg" # Fallback name                                                                          

            # Sanitize filename (optional, remove invalid chars)
            # You might want a more robust sanitization function                                                     
            img_filename = "".join(c for c in img_filename if c.isalnum() or c in ('.', '_', '-')).rstrip()                                                                                                                                
            if not img_filename: # Handle empty filename after sanitization                                          
                img_filename = f"image_{downloaded_count+1}.jpg"                                                     


            # Create full path to save the image                                                                     
            save_path = os.path.join(folder_name, img_filename)                                                      

            # Save the image                                                                                         
            print(f"Downloading: {img_url}  =>  {save_path}")                                                        
            with open(save_path, 'wb') as f:                                                                         
                for chunk in img_response.iter_content(8192): # Download in chunks                                   
                    f.write(chunk)                                                                                   
            downloaded_count += 1                                                                                    

        except requests.exceptions.RequestException as e:                                                            
            print(f"Error downloading {img_url}: {e}")                                                               
        except IOError as e:                                                                                         
            print(f"Error saving image {img_filename}: {e}")                                                         
        except Exception as e: # Catch other potential errors                                                        
             print(f"An unexpected error occurred for {img_url}: {e}")                                               


    print(f"\nFinished scraping. Downloaded {downloaded_count} images to '{folder_name}'.")                          

# --- Main execution block ---                                                                                       
if __name__ == "__main__":                                                                                           
    target_url = input("Enter the URL of the website to scrape images from: ")                                       
    # Basic validation for URL format (optional)                                                                     
    if not target_url.startswith(('http://', 'https://')):                                                           
        print("Invalid URL. Please include http:// or https://")                                                     
    else:                                                                                                            
        scrape_images(target_url)                                           
