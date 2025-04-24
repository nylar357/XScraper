import requests
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import base64
import re
import mimetypes
# --- Creation ---
# by nylar357
# email :bryce_polymorph@proton.me
# www.linkedin.com/in/brycezg
# Free Use but please give me some credit

# --- Configuration ---
# --- Configuration ---
TARGET_URL = 'https://hackernews.com' # <<<--- CHANGE THIS TO THE WEBSITE URL YOU WANT TO SCRAPE
SAVE_DIRECTORY = 'scraped_images'      # <<<--- CHANGE THIS IF YOU WANT A DIFFERENT FOLDER NAME
REQUEST_DELAY = 1                      # Delay in seconds between image download requests to be polite
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36' # Mimic a browser
# --- End Configuration ---

def sanitize_filename(filename):
    """Removes or replaces characters that are invalid in filenames."""
    # Remove invalid characters
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    # Replace spaces with underscores (optional)
    sanitized = sanitized.replace(" ", "_")
    # Limit length (optional)
    max_len = 200
    if len(sanitized) > max_len:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:max_len - len(ext)] + ext
    # Ensure filename is not empty
    if not sanitized:
        sanitized = "unnamed_image"
    return sanitized

def get_extension_from_content_type(content_type):
    """Guesses file extension based on MIME type."""
    if not content_type:
        return None
    # Clean up content-type (e.g., 'image/jpeg; charset=utf-8' -> 'image/jpeg')
    mime_type = content_type.split(';')[0].strip().lower()
    return mimetypes.guess_extension(mime_type)

def download_image(img_url, save_path, session):
    """Downloads a single image from a given URL."""
    try:
        print(f"Attempting to download: {img_url}")
        headers = {'User-Agent': USER_AGENT}
        # Use the session to make the request
        response = session.get(img_url, headers=headers, stream=True, timeout=20) # stream=True is important for large files
        response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)

        # --- Determine Filename and Extension ---
        parsed_url = urlparse(img_url)
        # Get path part and take the last component as potential filename
        potential_filename = os.path.basename(parsed_url.path)
        
        # Get Content-Type header
        content_type = response.headers.get('content-type')
        guessed_extension = get_extension_from_content_type(content_type)

        # Split the potential filename into name and extension
        base_name, original_ext = os.path.splitext(potential_filename)

        # Use guessed extension if the original one is missing or non-standard, or if there was no path
        final_extension = ""
        if guessed_extension and (not original_ext or len(original_ext) > 5 or not potential_filename) : # Heuristic: assume long extensions might be wrong
             final_extension = guessed_extension
        elif original_ext:
             final_extension = original_ext
        else: # Fallback if no extension found anywhere
             final_extension = ".img" 
             print(f"  [Warning] Could not determine extension for {img_url}. Using '.img'. Content-Type: {content_type}")

        # Create filename
        if base_name:
             filename = sanitize_filename(base_name + final_extension)
        else: # Generate a name if URL path was empty (e.g. https://site.com/getImage?)
             filename = sanitize_filename(f"image_{abs(hash(img_url))}{final_extension}")
        
        full_save_path = os.path.join(save_path, filename)
        
        # Avoid overwriting - add a number if file exists
        counter = 1
        while os.path.exists(full_save_path):
            name_part, ext_part = os.path.splitext(filename)
            # Remove previous counter if exists (e.g., image_1 -> image)
            name_part = re.sub(r'_\d+$', '', name_part) 
            full_save_path = os.path.join(save_path, f"{name_part}_{counter}{ext_part}")
            counter += 1

        # --- Save the Image ---
        with open(full_save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192): # Download in chunks
                f.write(chunk)
        print(f"  Successfully saved to: {full_save_path}")
        return True

    except requests.exceptions.RequestException as e:
        print(f"  [Error] Failed to download {img_url}: {e}")
    except Exception as e:
        print(f"  [Error] An unexpected error occurred while downloading {img_url}: {e}")
    return False


def save_data_uri(data_uri, save_path):
    """Saves an image from a data URI string."""
    try:
        print(f"Attempting to save data URI...")
        # Regex to parse data URI: data:[<mediatype>][;base64],<data>
        match = re.match(r'data:(image/(?P<type>[a-zA-Z+.-]+))?(;base64)?,(?P<data>.*)', data_uri, re.DOTALL)
        if not match:
            print("  [Error] Could not parse data URI.")
            return False

        data = match.group('data')
        img_type = match.group('type') if match.group('type') else 'png' # Default to png if type is missing

        # Decode base64 data
        img_data = base64.b64decode(data)

        # Generate filename
        extension = mimetypes.guess_extension(f'image/{img_type}') or f".{img_type}"
        filename = sanitize_filename(f"data_image_{abs(hash(data))}{extension}")
        full_save_path = os.path.join(save_path, filename)

        # Avoid overwriting
        counter = 1
        while os.path.exists(full_save_path):
             name_part, ext_part = os.path.splitext(filename)
             name_part = re.sub(r'_\d+$', '', name_part)
             full_save_path = os.path.join(save_path, f"{name_part}_{counter}{ext_part}")
             counter += 1

        with open(full_save_path, 'wb') as f:
            f.write(img_data)
        print(f"  Successfully saved data URI to: {full_save_path}")
        return True

    except base64.binascii.Error as e:
        print(f"  [Error] Failed to decode base64 data: {e}")
    except Exception as e:
        print(f"  [Error] An unexpected error occurred while saving data URI: {e}")
    return False


# --- Main Execution ---
if __name__ == "__main__":
    print(f"Starting image scrape for: {TARGET_URL}")
    print(f"Images will be saved to: {SAVE_DIRECTORY}")

    # Create the save directory if it doesn't exist
    os.makedirs(SAVE_DIRECTORY, exist_ok=True)

    # Use a session object for potential connection pooling and cookie handling
    session = requests.Session()
    session.headers.update({'User-Agent': USER_AGENT}) # Set user agent for the session

    try:
        # Fetch the HTML content of the page
        print(f"Fetching page content from {TARGET_URL}...")
        response = session.get(TARGET_URL, timeout=30)
        response.raise_for_status() # Check for HTTP errors
        print("Page content fetched successfully.")

        # Parse the HTML
        soup = BeautifulSoup(response.text, 'lxml') # You can also use 'html.parser' if lxml is not installed

        # Find all image tags
        img_tags = soup.find_all('img')
        print(f"Found {len(img_tags)} <img> tags.")

        downloaded_count = 0
        failed_count = 0

        # Loop through all found image tags
        for img in img_tags:
            img_src = img.get('src') # Use .get() to avoid errors if 'src' is missing

            if not img_src:
                print("  [Skipped] Found <img> tag with no 'src' attribute.")
                continue

            print(f"Processing src: {img_src[:100]}{'...' if len(img_src)>100 else ''}") # Print truncated src

            # Check for Data URIs
            if img_src.startswith('data:image'):
                if save_data_uri(img_src, SAVE_DIRECTORY):
                    downloaded_count += 1
                else:
                    failed_count +=1
                time.sleep(0.1) # Small delay even for data uris
                continue # Move to the next image tag

            # --- Handle Normal URLs (Absolute and Relative) ---
            try:
                # Convert relative URLs to absolute URLs
                # urljoin handles both absolute and relative paths correctly
                absolute_img_url = urljoin(TARGET_URL, img_src)
            except ValueError as e:
                print(f"  [Error] Could not form absolute URL from base '{TARGET_URL}' and src '{img_src}': {e}")
                failed_count += 1
                continue


            # Check if the URL looks downloadable (basic check)
            parsed_url = urlparse(absolute_img_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                 print(f"  [Skipped] Invalid or non-downloadable URL generated: {absolute_img_url}")
                 failed_count += 1
                 continue


            # Download the image
            if download_image(absolute_img_url, SAVE_DIRECTORY, session):
                downloaded_count += 1
            else:
                failed_count += 1

            # --- Polite Delay ---
            print(f"Waiting {REQUEST_DELAY} seconds...")
            time.sleep(REQUEST_DELAY)

        print("\n--- Scraping Summary ---")
        print(f"Total <img> tags processed: {len(img_tags)}")
        print(f"Images successfully downloaded/saved: {downloaded_count}")
        print(f"Download/save failures or skips: {failed_count}")
        print(f"Images saved in directory: '{SAVE_DIRECTORY}'")

    except requests.exceptions.RequestException as e:
        print(f"\n[Fatal Error] Could not fetch the initial page {TARGET_URL}: {e}")
    except Exception as e:
        print(f"\n[Fatal Error] An unexpected error occurred during scraping: {e}")
