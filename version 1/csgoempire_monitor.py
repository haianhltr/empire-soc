#!/usr/bin/env python3
"""
csgoempire_monitor.py
Complete CSGOEmpire WebSocket monitor with item name extraction
"""

import sqlite3
import json
import re
import time
import argparse
import sys
from datetime import datetime
from websocket import create_connection, WebSocketException
import requests

# Fix Unicode output
sys.stdout.reconfigure(encoding='utf-8')

def create_database():
    """Create database schema"""
    conn = sqlite3.connect('csgoempire_monitor.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER UNIQUE,
        market_name TEXT,
        type TEXT,
        category TEXT,
        sub_type TEXT,
        rarity TEXT,
        wear_name TEXT,
        wear_value REAL,
        market_value INTEGER,
        suggested_price INTEGER,
        purchase_price INTEGER,
        above_recommended_price REAL,
        published_at TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS auctions (
        auction_id INTEGER PRIMARY KEY,
        item_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES items (item_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS auction_updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auction_id INTEGER,
        item_id INTEGER,
        timestamp TEXT,
        chrome_timestamp REAL,
        highest_bid INTEGER,
        highest_bidder INTEGER,
        number_of_bids INTEGER,
        ends_at INTEGER,
        above_recommended_price REAL,
        FOREIGN KEY (auction_id) REFERENCES auctions (auction_id),
        FOREIGN KEY (item_id) REFERENCES items (item_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bidders (
        bidder_id INTEGER PRIMARY KEY,
        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_bids INTEGER DEFAULT 0,
        total_spent INTEGER DEFAULT 0
    )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_market_name ON items (market_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_type ON items (type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_auction_updates_auction_id ON auction_updates (auction_id)')
    
    conn.commit()
    conn.close()
    print("Database schema created!")

def pick_target_ws_url(port=9222, match_title=None, match_url=None):
    """Find Chrome DevTools WebSocket URL"""
    info_url = f"http://127.0.0.1:{port}/json"
    tabs = requests.get(info_url, timeout=5).json()
    
    def score(t):
        s = 0
        if t.get("type") == "page":
            s += 2
        title = (t.get("title") or "").lower()
        url = (t.get("url") or "").lower()
        if match_title and match_title.lower() in title:
            s += 3
        if match_url and match_url.lower() in url:
            s += 3
        return s

    tabs_sorted = sorted(tabs, key=score, reverse=True)
    if not tabs_sorted:
        return None

    top = tabs_sorted[0]
    if match_title or match_url:
        title = (top.get("title") or "").lower()
        url = (top.get("url") or "").lower()
        ok_title = (not match_title) or (match_title.lower() in title)
        ok_url = (not match_url) or (match_url.lower() in url)
        if not (ok_title and ok_url):
            return None

    return top.get("webSocketDebuggerUrl")

def extract_item_info_simple(payload):
    """Simple item extraction using string methods"""
    items = []
    
    if '"new_item"' not in payload:
        return items
    
    # Find the start of the item data
    start = payload.find('"new_item",[')
    if start == -1:
        return items
    
    # Extract the item data section
    item_section = payload[start + 11:]  # Skip '"new_item",['
    
    # Find the end of the array
    bracket_count = 0
    end_pos = 0
    for i, char in enumerate(item_section):
        if char == '[':
            bracket_count += 1
        elif char == ']':
            bracket_count -= 1
            if bracket_count == 0:
                end_pos = i
                break
    
    if end_pos == 0:
        return items
    
    item_data = item_section[:end_pos]
    
    # Extract individual fields using simple string operations
    item_info = {}
    
    # Extract ID
    id_match = re.search(r'"id":(\d+)', item_data)
    if id_match:
        item_info['id'] = int(id_match.group(1))
    
    # Extract market name
    name_match = re.search(r'"market_name":"([^"]+)"', item_data)
    if name_match:
        item_info['market_name'] = name_match.group(1)
    
    # Extract type
    type_match = re.search(r'"type":"([^"]+)"', item_data)
    if type_match:
        item_info['type'] = type_match.group(1)
    
    # Extract market value
    value_match = re.search(r'"market_value":(\d+)', item_data)
    if value_match:
        item_info['market_value'] = int(value_match.group(1))
    
    # Extract suggested price
    suggested_match = re.search(r'"suggested_price":(\d+)', item_data)
    if suggested_match:
        item_info['suggested_price'] = int(suggested_match.group(1))
    
    # Extract purchase price
    purchase_match = re.search(r'"purchase_price":(\d+)', item_data)
    if purchase_match:
        item_info['purchase_price'] = int(purchase_match.group(1))
    
    # Extract above recommended price
    above_match = re.search(r'"above_recommended_price":([\d.-]+)', item_data)
    if above_match:
        item_info['above_recommended_price'] = float(above_match.group(1))
    
    # Extract wear
    wear_match = re.search(r'"wear":([\d.]+)', item_data)
    if wear_match:
        item_info['wear'] = float(wear_match.group(1))
    
    # Extract wear name
    wear_name_match = re.search(r'"wear_name":"([^"]+)"', item_data)
    if wear_name_match:
        item_info['wear_name'] = wear_name_match.group(1)
    
    # Extract published at
    published_match = re.search(r'"published_at":"([^"]+)"', item_data)
    if published_match:
        item_info['published_at'] = published_match.group(1)
    
    # Extract category
    category_match = re.search(r'"category":"([^"]+)"', item_data)
    if category_match:
        item_info['category'] = category_match.group(1)
    
    # Extract sub_type
    sub_type_match = re.search(r'"sub_type":"([^"]+)"', item_data)
    if sub_type_match:
        item_info['sub_type'] = sub_type_match.group(1)
    
    # Extract rarity
    rarity_match = re.search(r'"rarity":"([^"]+)"', item_data)
    if rarity_match:
        item_info['rarity'] = rarity_match.group(1)
    
    if 'id' in item_info:
        items.append(item_info)
    
    return items

def process_websocket_message(payload, timestamp, chrome_timestamp, conn):
    """Process WebSocket message and store in database"""
    cursor = conn.cursor()
    
    try:
        # Process new items
        if 'new_item' in payload:
            items = extract_item_info_simple(payload)
            
            for item in items:
                item_id = item['id']
                
                # Insert item
                cursor.execute('''
                    INSERT OR REPLACE INTO items 
                    (item_id, market_name, type, category, sub_type, rarity, wear_name, wear_value,
                     market_value, suggested_price, purchase_price, above_recommended_price, published_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    item_id, item.get('market_name'), item.get('type'), item.get('category'),
                    item.get('sub_type'), item.get('rarity'), item.get('wear_name'), item.get('wear'),
                    item.get('market_value'), item.get('suggested_price'), item.get('purchase_price'),
                    item.get('above_recommended_price'), item.get('published_at')
                ))
                
                print(f"[NEW ITEM] {item.get('market_name', 'Unknown')} - ${item.get('market_value', 0):,}")
        
        # Process auction updates
        elif 'auction_update' in payload:
            auction_match = re.search(r'"auction_update",\[(.*?)\]', payload)
            if auction_match:
                try:
                    auction_data = json.loads('[' + auction_match.group(1) + ']')
                    
                    for auction in auction_data:
                        auction_id = auction['id']
                        
                        # Insert auction
                        cursor.execute('INSERT OR IGNORE INTO auctions (auction_id) VALUES (?)', (auction_id,))
                        
                        # Insert auction update
                        cursor.execute('''
                            INSERT INTO auction_updates 
                            (auction_id, timestamp, chrome_timestamp, highest_bid, highest_bidder, 
                             number_of_bids, ends_at, above_recommended_price)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (
                            auction_id, timestamp, chrome_timestamp,
                            auction['auction_highest_bid'], auction['auction_highest_bidder'],
                            auction['auction_number_of_bids'], auction['auction_ends_at'],
                            auction['above_recommended_price']
                        ))
                        
                        # Update bidder stats
                        bidder_id = auction['auction_highest_bidder']
                        cursor.execute('INSERT OR IGNORE INTO bidders (bidder_id) VALUES (?)', (bidder_id,))
                        cursor.execute('''
                            UPDATE bidders SET 
                                last_seen = CURRENT_TIMESTAMP,
                                total_bids = total_bids + 1,
                                total_spent = total_spent + ?
                            WHERE bidder_id = ?
                        ''', (auction['auction_highest_bid'], bidder_id))
                        
                        print(f"[AUCTION] {auction_id}: ${auction['auction_highest_bid']:,} by {bidder_id} ({auction['auction_number_of_bids']} bids)")
                        
                except json.JSONDecodeError:
                    pass
        
        conn.commit()
        
    except Exception as e:
        print(f"Error processing message: {e}")
        conn.rollback()

def monitor_websocket(port=9222, match_url="csgoempire"):
    """Main monitoring function"""
    print("Setting up database...")
    create_database()
    
    print(f"Connecting to Chrome DevTools on port {port}...")
    try:
        ws_debug_url = pick_target_ws_url(port, None, match_url)
    except Exception as e:
        print(f"Could not query DevTools: {e}")
        return
    
    if not ws_debug_url:
        print("No matching Chrome tab found")
        return
    
    print(f"Connecting to CDP: {ws_debug_url}")
    
    try:
        cdp = create_connection(ws_debug_url, timeout=10)
    except Exception as e:
        print(f"Could not connect to CDP: {e}")
        return
    
    # Connect to database
    conn = sqlite3.connect('csgoempire_monitor.db')
    
    id_counter = [1]
    
    def send(method, params=None):
        msg = {"id": id_counter[0], "method": method}
        if params:
            msg["params"] = params
        cdp.send(json.dumps(msg))
        id_counter[0] += 1
    
    # Enable Network events
    send("Network.enable", {})
    
    print("Starting real-time monitoring... (Ctrl+C to stop)")
    print("=" * 60)
    
    try:
        while True:
            raw = cdp.recv()
            if not raw:
                continue
            
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            
            method = msg.get("method")
            params = msg.get("params", {})
            
            if not method:
                continue
            
            # Process WebSocket frames
            if method == "Network.webSocketFrameReceived":
                frame = params.get("response", {}) or {}
                payload = frame.get("payloadData")
                
                if payload and match_url.lower() in (params.get("url", "") or "").lower():
                    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"
                    chrome_timestamp = params.get("timestamp")
                    
                    process_websocket_message(payload, timestamp, chrome_timestamp, conn)
    
    except KeyboardInterrupt:
        print("\nStopping monitor...")
    except WebSocketException as e:
        print(f"WebSocket error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        conn.close()
        try:
            cdp.close()
        except:
            pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CSGOEmpire WebSocket Monitor")
    parser.add_argument("--port", type=int, default=9222, help="Chrome DevTools port")
    parser.add_argument("--match-url", type=str, default="csgoempire", help="URL filter")
    
    args = parser.parse_args()
    monitor_websocket(args.port, args.match_url)
