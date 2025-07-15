import requests
import json
from bs4 import BeautifulSoup
import os

# --- This is a special script just for debugging ---
PAGE_URL = "https://tixel.com/us/festival-tickets/burning-man-tickets"

def debug_data_structure():
    """This function will print the top-level 'keys' of the data object."""
    print("--- Starting Debug Run ---")
    try:
        response = requests.get(PAGE_URL, headers={'User-Agent': 'My Debug Script'})
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NUXT_DATA__'})
        
        if not script_tag:
            print("❌ Could not find the __NUXT_DATA__ script tag.")
            return

        raw_data = json.loads(script_tag.string)
        data_object = None

        if isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict):
                    data_object = item
                    break
        elif isinstance(raw_data, dict):
            data_object = raw_data

        if not data_object:
            print("❌ Could not find a usable data dictionary inside the JSON.")
            return
        
        # This is the important part: print the "map" of the data
        print("✅ Success! Found the main data object. Here is its structure (keys):")
        print(list(data_object.keys()))
        print("--- End of Debug Run ---")

    except Exception as e:
        print(f"An error occurred during the debug run: {e}")

if __name__ == "__main__":
    debug_data_structure()
