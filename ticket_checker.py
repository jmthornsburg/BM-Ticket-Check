import requests
import json
from bs4 import BeautifulSoup
import time
import os

# --- Configuration ---
PAGE_URL = "https://tixel.com/us/festival-tickets/burning-man-tickets"
MAX_PRICE = int(os.environ.get('MAX_PRICE', 700))
NTFY_TOPIC = os.environ.get('NTFY_TOPIC')

def final_ticket_checker():
    """This definitive script uses the verified data path to find tickets."""
    print(f"Checking for tickets under ${MAX_PRICE}...")

    if not NTFY_TOPIC:
        print("❌ ERROR: NTFY_TOPIC secret is not set in GitHub repository settings.")
        return False

    try:
        response = requests.get(PAGE_URL, headers={'User-Agent': 'Final Tixel Checker'})
        
        if response.status_code != 200:
            print(f"Error downloading page: Status {response.status_code}")
            return False

        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': '__NUXT_DATA__'})
        
        if not script_tag:
            print("❌ Could not find the __NUXT_DATA__ script tag.")
            return False

        raw_data = json.loads(script_tag.string)

        # This is the verified correct data path from your debug file
        data_object = raw_data[1]
        listings = data_object['pinia']['EventStore']['current']['tickets']['available']

        if not listings:
            print("No tickets currently listed.")
            return False

        print(f"Found {len(listings)} tickets available. Checking prices...")

        for ticket in listings:
            if not isinstance(ticket, dict):
                continue
                
            price_in_cents = ticket.get('purchasePrice')
            if price_in_cents and (price_in_cents / 100) <= MAX_PRICE:
                price_dollars = price_in_cents / 100
                ticket_id = ticket.get('id')
                ticket_url = f"https://tixel.com/tickets/{ticket_id}"
                
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

    except KeyError as e:
        print(f"A key was not found, the website structure has likely changed. Missing key: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return False

if __name__ == "__main__":
    if final_ticket_checker():
        print("Found a matching ticket.")
    else:
        print("No matching ticket found in this run.")
