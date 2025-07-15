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
    """Downloads page HTML, extracts embedded JSON, and checks for tickets."""
    print(f"Checking for tickets under ${MAX_PRICE}...")

    if not NTFY_TOPIC:
        print("❌ ERROR: NTFY_TOPIC secret is not set in GitHub repository settings.")
        return False

    try:
        response = requests.get(PAGE_URL, headers={'User-Agent': 'My Ticket Checker Script v6.0'})
        
        if response.status_code != 200:
            print(f"Error: Failed to download page, status code {response.status_code}")
            return False

        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NUXT_DATA__'})
        
        if not script_tag:
            print("❌ Could not find the embedded data script tag.")
            return False

        data = json.loads(script_tag.string)

        # *** This section is now more robust to prevent errors ***
        # The path to the data can sometimes vary slightly.
        listings = []
        if data.get('payload') and data['payload'].get('results'):
            search_results = data['payload']['results']
            if search_results and isinstance(search_results[0], dict):
                listings = search_results[0].get('listings', [])
        
        # Fallback for another possible data structure
        elif data.get('data') and isinstance(data['data'], list) and len(data['data']) > 0:
            potential_listings = data['data'][0].get('listings')
            if potential_listings:
                 listings = potential_listings


        if not listings:
            print("No tickets currently listed.")
            return False

        for ticket in listings:
            # Ensure the ticket item itself is a dictionary before proceeding
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
