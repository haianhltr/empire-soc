#!/usr/bin/env python3
"""
enhanced_item_parser.py
Enhanced parser to extract item names and details from WebSocket data
"""

import sqlite3
import json
import re
from datetime import datetime

def create_enhanced_database():
    """Create enhanced database schema with item details"""
    conn = sqlite3.connect('csgoempire_enhanced.db')
    cursor = conn.cursor()
    
    # Enhanced items table with full item details
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
        icon_url TEXT,
        preview_id TEXT,
        name_color TEXT,
        is_commodity INTEGER,
        price_is_unreliable INTEGER,
        published_at TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Auction table linking to items
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS auctions (
        id INTEGER PRIMARY KEY,
        auction_id INTEGER UNIQUE,
        item_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (item_id) REFERENCES items (item_id)
    )
    ''')
    
    # Auction updates with item context
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
    
    # Bidders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bidders (
        bidder_id INTEGER PRIMARY KEY,
        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_bids INTEGER DEFAULT 0,
        total_spent INTEGER DEFAULT 0
    )
    ''')
    
    # Item listings with full details
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS item_listings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        timestamp TEXT,
        chrome_timestamp REAL,
        auction_ends_at INTEGER,
        FOREIGN KEY (item_id) REFERENCES items (item_id)
    )
    ''')
    
    # Item deletions
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS item_deletions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        timestamp TEXT,
        chrome_timestamp REAL,
        FOREIGN KEY (item_id) REFERENCES items (item_id)
    )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_market_name ON items (market_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_type ON items (type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_category ON items (category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_auction_updates_item_id ON auction_updates (item_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_auction_updates_auction_id ON auction_updates (auction_id)')
    
    conn.commit()
    conn.close()
    print("Enhanced database schema created!")

def parse_enhanced_websocket_data(filename):
    """Parse WebSocket data with full item details"""
    conn = sqlite3.connect('csgoempire_enhanced.db')
    cursor = conn.cursor()
    
    # Map auction_id to item_id for auction updates
    auction_to_item = {}
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                payload = data['payload']
                timestamp = data['t']
                chrome_timestamp = float(data['t'].split('chrome_ts=')[1].split(')')[0]) if 'chrome_ts=' in data['t'] else None
                
                # Parse new items with full details
                if 'new_item' in payload:
                    item_match = re.search(r'"new_item",\[(.*?)\]', payload)
                    if item_match:
                        item_data = json.loads('[' + item_match.group(1) + ']')
                        
                        for item in item_data:
                            item_id = item['id']
                            
                            # Extract item search details
                            item_search = item.get('item_search', {})
                            
                            # Insert item with full details
                            cursor.execute('''
                                INSERT OR REPLACE INTO items 
                                (item_id, market_name, type, category, sub_type, rarity, wear_name, wear_value,
                                 market_value, suggested_price, purchase_price, above_recommended_price,
                                 icon_url, preview_id, name_color, is_commodity, price_is_unreliable, published_at)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                item_id,
                                item.get('market_name'),
                                item.get('type'),
                                item_search.get('category'),
                                item_search.get('sub_type'),
                                item_search.get('rarity'),
                                item.get('wear_name'),
                                item.get('wear'),
                                item.get('market_value'),
                                item.get('suggested_price'),
                                item.get('purchase_price'),
                                item.get('above_recommended_price'),
                                item.get('icon_url'),
                                item.get('preview_id'),
                                item.get('name_color'),
                                item.get('is_commodity', 0),
                                item.get('price_is_unreliable', 0),
                                item.get('published_at')
                            ))
                            
                            # Record item listing
                            cursor.execute('''
                                INSERT INTO item_listings (item_id, timestamp, chrome_timestamp, auction_ends_at)
                                VALUES (?, ?, ?, ?)
                            ''', (item_id, timestamp, chrome_timestamp, item.get('auction_ends_at')))
                            
                            print(f"[NEW ITEM] {item.get('market_name', 'Unknown')} - ${item.get('market_value', 0):,}")
                
                # Parse auction updates
                elif 'auction_update' in payload:
                    auction_match = re.search(r'"auction_update",\[(.*?)\]', payload)
                    if auction_match:
                        auction_data = json.loads('[' + auction_match.group(1) + ']')
                        
                        for auction in auction_data:
                            auction_id = auction['id']
                            
                            # Try to find item_id for this auction
                            item_id = auction_to_item.get(auction_id)
                            
                            # Insert auction if not exists
                            cursor.execute('INSERT OR IGNORE INTO auctions (auction_id, item_id) VALUES (?, ?)', 
                                         (auction_id, item_id))
                            
                            # Insert auction update
                            cursor.execute('''
                                INSERT INTO auction_updates 
                                (auction_id, item_id, timestamp, chrome_timestamp, highest_bid, highest_bidder, 
                                 number_of_bids, ends_at, above_recommended_price)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                auction_id, item_id, timestamp, chrome_timestamp,
                                auction['auction_highest_bid'], auction['auction_highest_bidder'],
                                auction['auction_number_of_bids'], auction['auction_ends_at'],
                                auction['above_recommended_price']
                            ))
                            
                            # Update bidder stats
                            bidder_id = auction['auction_highest_bidder']
                            cursor.execute('''
                                INSERT OR IGNORE INTO bidders (bidder_id) VALUES (?)
                            ''', (bidder_id,))
                            cursor.execute('''
                                UPDATE bidders SET 
                                    last_seen = CURRENT_TIMESTAMP,
                                    total_bids = total_bids + 1,
                                    total_spent = total_spent + ?
                                WHERE bidder_id = ?
                            ''', (auction['auction_highest_bid'], bidder_id))
                
                # Parse deleted items
                elif 'deleted_item' in payload:
                    deleted_match = re.search(r'"deleted_item",\[(.*?)\]', payload)
                    if deleted_match:
                        deleted_data = deleted_match.group(1)
                        item_ids = [int(x.strip()) for x in deleted_data.split(',')]
                        
                        for item_id in item_ids:
                            cursor.execute('''
                                INSERT INTO item_deletions (item_id, timestamp, chrome_timestamp)
                                VALUES (?, ?, ?)
                            ''', (item_id, timestamp, chrome_timestamp))
                
            except Exception as e:
                print(f"Error parsing line {line_num}: {e}")
                continue
    
    conn.commit()
    conn.close()
    print("Enhanced WebSocket data imported successfully!")

def show_item_analysis():
    """Show analysis with item names"""
    conn = sqlite3.connect('csgoempire_enhanced.db')
    cursor = conn.cursor()
    
    print("\n=== Item Analysis ===")
    
    # Show items by category
    cursor.execute('''
        SELECT category, COUNT(*) as count, AVG(market_value) as avg_value
        FROM items 
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
    ''')
    
    print("\nItems by Category:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} items, avg value: ${row[2]:,.0f}")
    
    # Show most expensive items
    cursor.execute('''
        SELECT market_name, market_value, type, wear_name
        FROM items 
        ORDER BY market_value DESC
        LIMIT 10
    ''')
    
    print("\nMost Expensive Items:")
    for row in cursor.fetchall():
        print(f"  {row[0]} - ${row[1]:,} ({row[2]}, {row[3]})")
    
    # Show auction activity with item names
    cursor.execute('''
        SELECT i.market_name, a.auction_id, COUNT(au.id) as update_count,
               MIN(au.highest_bid) as min_bid, MAX(au.highest_bid) as max_bid
        FROM items i
        JOIN auctions a ON i.item_id = a.item_id
        JOIN auction_updates au ON a.auction_id = au.auction_id
        GROUP BY a.auction_id
        ORDER BY update_count DESC
        LIMIT 10
    ''')
    
    print("\nMost Active Auctions with Item Names:")
    for row in cursor.fetchall():
        print(f"  {row[0]} (Auction {row[1]}): {row[2]} updates, ${row[3]:,} → ${row[4]:,}")
    
    # Show recent item listings
    cursor.execute('''
        SELECT market_name, market_value, published_at
        FROM items 
        ORDER BY published_at DESC
        LIMIT 10
    ''')
    
    print("\nRecent Item Listings:")
    for row in cursor.fetchall():
        print(f"  {row[0]} - ${row[1]:,} ({row[2][:19]})")
    
    conn.close()

if __name__ == "__main__":
    create_enhanced_database()
    parse_enhanced_websocket_data("csgoempire_websocket_data.jsonl")
    show_item_analysis()
