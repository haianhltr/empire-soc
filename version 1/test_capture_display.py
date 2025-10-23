import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

print("Testing with your captured data...")
print("=" * 60)

# Read one line from your captured data
with open('csgoempire_websocket_data.jsonl', 'r', encoding='utf-8') as f:
    count = 0
    for line in f:
        data = json.loads(line)
        payload = data.get('payload', '')
        
        if 'new_item' in payload:
            # Extract item name
            name_match = re.search(r'"market_name":"([^"]+)"', payload)
            value_match = re.search(r'"market_value":(\d+)', payload)
            
            if name_match:
                item_name = name_match.group(1)
                item_value = value_match.group(1) if value_match else "0"
                print(f'[NEW ITEM] {item_name} - ${int(item_value):,}')
                count += 1
                
            if count >= 5:  # Show first 5 items
                break
        
        elif 'auction_update' in payload:
            # Extract auction info
            auction_match = re.search(r'"id":(\d+).*?"auction_highest_bid":(\d+).*?"auction_highest_bidder":(\d+).*?"auction_number_of_bids":(\d+)', payload)
            if auction_match:
                auction_id = auction_match.group(1)
                bid = auction_match.group(2)
                bidder = auction_match.group(3)
                num_bids = auction_match.group(4)
                print(f'[AUCTION] {auction_id}: ${int(bid):,} by {bidder} ({num_bids} bids)')
                count += 1
                
            if count >= 10:  # Show 10 total events
                break

print()
print("=" * 60)
print("THIS IS WHAT YOU'LL SEE IN REAL-TIME!")
print("When the monitor is running, every WebSocket message")
print("will be parsed and displayed like this.")
print("=" * 60)

