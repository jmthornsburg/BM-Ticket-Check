import requests
import json
from bs4 import BeautifulSoup
import time
import os

PAGE_URL = "https://tixel.com/us/festival-tickets/burning-man-tickets"
MAX_PRICE = int(os.environ.get('MAX_PRICE', 780))
NTFY_TOPIC = os.environ.get('NTFY_TOPIC')

def final_proof_checker():
    print(f"--- FINAL ATTEMPT ---")
    print(f"Checking for tickets under ${MAX_PRICE}...")

    if not NTFY_TOPIC:
        print("❌ ERROR: NTFY_TOPIC secret is not set.")
        return False, None

    try:
        response = requests.get(PAGE_URL, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'})
        
        if response.status_code != 200:
            print(f"Error downloading page: Status {response.status_code}")
            return False, None

        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NUXT_DATA__'})
        
        if not script_tag:
            print("❌ Could not find the __NUXT_DATA__ script tag.")
            return False, response.text # Return the HTML content for debugging

        # Save the captured data for proof
        with open("debug_output.json", "w") as f:
            f.write(script_tag.string)

        raw_data = json.loads(script_tag.string)
        
        data_object = None
        if isinstance(raw_data, list) and len(raw_data) > 1 and isinstance(raw_data[1], dict):
            data_object = raw_data[1]
        elif isinstance(raw_data, dict):
            data_object = raw_data

        if not data_object:
            print("❌ Could not find a usable dictionary in the JSON data.")
            return False, script_tag.string

        listings = data_object.get('pinia', {}).get('EventStore', {}).get('current', {}).get('tickets', {}).get('available', [])

        if not isinstance(listings, list):
            print(f"❌ Expected 'available' to be a list, but found {type(listings)}.")
            return False, script_tag.string
            
        if not listings:
            print("✅ Script ran successfully, but the 'available' tickets list from the server was empty.")
            return False, script_tag.string

        print(f"✅ Found {len(listings)} tickets in the data. Checking prices...")

        for ticket in listings:
            if isinstance(ticket, dict):
                price_in_cents = ticket.get('purchasePrice')
                if price_in_cents and (price_in_cents / 100) <= MAX_PRICE:
                    price_dollars = price_in_cents / 100
                    ticket_id = ticket.get('id')
                    ticket_url = f"https://tixel.com/tickets/{ticket_id}"
                    
                    print(f"🎉 FOUND ONE! Price: ${price_dollars}")
                    
                    requests.post(
                        f"https://ntfy.sh/{NTFY_TOPIC}",
                        data=f"Ticket found for ${price_dollars}!".encode(encoding='utf-8'),
                        headers={"Title": "Burning Man Ticket Alert!", "Priority": "max", "Tags": "tada", "Click": ticket_url}
                    )
                    return True, None
        
        print("No tickets matched the price criteria.")
        return False, script_tag.string


    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return False, None

if __name__ == "__main__":
    found_ticket, debug_data = final_proof_checker()
    if not found_ticket:
        print("--- Run complete. No notification sent. ---")
