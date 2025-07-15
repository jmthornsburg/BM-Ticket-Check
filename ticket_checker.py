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
        response = requests.get(PAGE_URL, headers={'User-Agent': 'My Ticket Checker Script v10.0 (Final)'})
        
        if response.status_code != 200:
            print(f"Error: Failed to download page, status code {response.status_code}")
            return False

        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NUXT_DATA__'})
        
        if not script_tag:
            print("❌ Could not find the embedded data script tag.")
            return False

        raw_data = json.loads(script_tag.string)

        data_object = None
        if isinstance(raw_data, list):
            for item in raw_data:
                if isinstance(item, dict) and 'pinia' in item:
                    data_object = item
                    break
        elif isinstance(raw_data, dict):
            data_object = raw_data

        if not (data_object and 'pinia' in data_object and 'EventStore' in data_object['pinia']):
             print("❌ Could not find the 'pinia' or 'EventStore' keys in the data.")
             return False

        # *** FINAL FIX: Check if the 'available' data is a list before using it ***
        listings_data = data_object['pinia']['EventStore'].get('entity', {}).get('tickets', {}).get('available', [])
        
        listings = []
        if isinstance(listings_data, list):
            listings = listings_data
        else:
            print(f"Data for 'available' tickets was not a list (found {type(listings_data)}). Assuming no listings.")

        if not listings:
            print("No tickets currently listed.")
            return False

        for ticket in listings:
            if not isinstance(ticket, dict):
                continue
                
            price_in_cents = ticket.get('purchasePrice')
            if price_in_cents and (price_in_cents / 100) <= MAX_PRICE:
                price_dollars = price_in_cents / 100
                ticket_url = f"https://tixel.com/u/{ticket.get('seller', {}).get('id')}"
                
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
