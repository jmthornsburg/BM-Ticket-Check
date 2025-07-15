# This is a special script to CAPTURE data, not check for tickets.
import requests
import json
from bs4 import BeautifulSoup

def capture_data():
    """Finds the __NUXT_DATA__ and saves its content to a file."""
    print("--- Starting Data Capture Run ---")
    try:
        response = requests.get("https://tixel.com/us/festival-tickets/burning-man-tickets", headers={'User-Agent': 'Data Capture Script'})
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NUXT_DATA__'})
        
        if not script_tag:
            print("❌ FAILED: Could not find the __NUXT_DATA__ script tag.")
            return

        # Save the raw JSON content to a file
        with open("debug_output.json", "w") as f:
            f.write(script_tag.string)
            
        print("✅ SUCCESS: Data has been saved to debug_output.json.")

    except Exception as e:
        print(f"An error occurred during data capture: {e}")

if __name__ == "__main__":
    capture_data()
