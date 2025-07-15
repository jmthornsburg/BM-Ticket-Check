import requests
import json
from bs4 import BeautifulSoup
import time
import os

# --- Configuration ---
PAGE_URL = "https://tixel.com/us/festival-tickets/burning-man-tickets"
MAX_PRICE = int(os.environ.get('MAX_PRICE', 550))
NTFY_TOPIC = os.environ.get('NTFY_TOPIC')

# --- Main Script ---
def check_for_tickets_from_html():
    """Downloads the page HTML, extracts the embedded JSON data, and checks for tickets."""
    print(f"Checking for tickets under ${MAX_PRICE}...")

    if not NTFY_TOPIC:
        print("❌ ERROR: NTFY_TOPIC secret is not set in GitHub repository settings.")
        return False

    try:
        response = requests.get(PAGE_URL, headers={'User-Agent': 'My Ticket Checker Script v8.0'})
        
        if response.status_code != 200:
            print(f"Error: Failed to download page, status code {response.status_code}")
            return False

        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NUXT_DATA__'})
        
        if not script_tag:
            print("❌ Could not find the embedded data script tag.")
            return False

        # Load the raw data from the script tag
        raw_data = json.loads(script_tag.string)

        # *** NEW: This section correctly handles the data if it's a list ***
        data_object = None
        if isinstance(raw_data, list):
            # If the raw data is a list, find the first dictionary inside it
            for item in raw_data:
                if isinstance(item, dict):
                    data_object = item
                    break
        elif isinstance(raw_data, dict):
            # If it's a dictionary, use it directly
            data_object = raw_data

        if not data_object:
            print("❌ Could not find a usable data object inside the JSON.")
            return False

        # Proceed using the found data_object
        listings = []
        if data_object.get('payload') and isinstance(data_object.get('payload'), dict) and data_object['payload'].get('results'):
            search_results = data_object['payload']['results']
            if search_results and isinstance(search_results[0], dict):
                listings = search_results[0].get('listings', [])

        if not listings:
            print("No tickets currently listed in the expected data structure.")
            return False

        for ticket in listings:
            if not isinstance(ticket, dict):
                continue
                
            price_in_cents = ticket.get('price_cents')
            if price_in_cents and (price_in_cents / 100) <= MAX_PRICE:
                price_dollars = price_in_cents / 100
                ticket_url = ticket.get('url')
                print(f"🎉 FOUND ONE! Price: ${price_dollars}")
                
                requests.post(
                    f"https://ntfy.sh/{NTFY_TOPIC}",
                    data=f"Ticket found for ${price_dollars}. Click to view!".encode(encoding='utf-8'),
                    headers={
                        "Title": "Burning Man Ticket Alert!",
                        "Priority": "urgent",
                        "Tags": "tada",
                        "Click": ticket_url
                    }
                )
                return True

    except Exception as e:
        print(f"An error occurred: {e}")
    return False

if __name__ == "__main__":
    if check_for_tickets_from_html():
        print("Found a ticket, stopping script.")
    else:
        print("No matching ticket found in this run.")
