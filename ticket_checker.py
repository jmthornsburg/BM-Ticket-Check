import requests
import json
from bs4 import BeautifulSoup
import time
import os

# --- Configuration ---
PAGE_URL = "https://tixel.com/us/festival-tickets/burning-man-tickets"
MAX_PRICE = int(os.environ.get('MAX_PRICE', 700)) # Increased default for testing
NTFY_TOPIC = os.environ.get('NTFY_TOPIC')

# --- Main Script ---
def check_for_tickets_from_html():
    """Downloads the page HTML, extracts the embedded JSON data, and checks for tickets."""
    print(f"Checking for tickets under ${MAX_PRICE}...")

    if not NTFY_TOPIC:
        print("❌ ERROR: NTFY_TOPIC secret is not set in GitHub repository settings.")
        return False

    try:
        response = requests.get(PAGE_URL, headers={'User-Agent': 'My Ticket Checker Script v11.0 (Final)'})
        
        if response.status_code != 200:
            print(f"Error: Failed to download page, status code {response.status_code}")
            return False

        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NUXT_DATA__'})
        
        if not script_tag:
            print("❌ Could not find the embedded data script tag.")
            return False

        raw_data = json.loads(script_tag.string)

        # *** FINAL, CORRECTED DATA PATH BASED ON YOUR DEBUG FILE ***
        data_object = None
        if isinstance(raw_data, list) and len(raw_data) > 1:
            # The main data object is the second item in the list
            if isinstance(raw_data[1], dict):
                data_object = raw_data[1]

        if not data_object:
            print("❌ Could not find a usable data object inside the JSON.")
            return False

        # The path is now: pinia -> EventStore -> current -> tickets -> available
        listings = data_object.get('pinia', {}).get('EventStore', {}).get('current', {}).get('tickets', {}).get('available', [])

        if not listings:
            print("No tickets currently listed in the 'available' data field.")
            return False

        print(f"Found {len(listings)} tickets available. Checking prices...")

        for ticket in listings:
            if not isinstance(ticket, dict):
                continue
                
            # The price is in 'purchasePrice'
            price_in_cents = ticket.get('purchasePrice')
            if price_in_cents and (price_in_cents / 100) <= MAX_PRICE:
                price_dollars = price_in_cents / 100
                ticket_id = ticket.get('id')
                ticket_url = f"https://tixel.com/tickets/{ticket_id}" if ticket_id else "URL not found"
                
                print(f"🎉 FOUND ONE! Price: ${price_dollars}")
                
                requests.post(
                    f"https://ntfy.sh/{NTFY_TOPIC}",
                    data=f"Ticket found for ${price_dollars}. Click to view!".encode(encoding='utf-8'),
                    headers={
                        "Title": "Burning Man Ticket Alert!",
                        "Priority": "max",
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
