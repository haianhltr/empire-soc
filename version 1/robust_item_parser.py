#!/usr/bin/env python3
"""
robust_item_parser.py
Robust parser that handles malformed JSON in WebSocket data
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
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_market_name ON items (market_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_type ON items (type)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_category ON items (category)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_auction_updates_item_id ON auction_updates (item_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_auction_updates_auction_id ON auction_updates (auction_id)')
    
    conn.commit()
    conn.close()
    print("Enhanced database schema created!")

def extract_item_info_from_payload(payload):
    """Extract item information from malformed JSON payload"""
    items = []
    
    # Find all new_item entries
    new_item_matches = re.findall(r'"new_item",\[(.*?)\]', payload)
    
    for match in new_item_matches:
        try:
            # Try to parse as JSON first
            item_data = json.loads('[' + match + ']')
            items.extend(item_data)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract fields manually
            item_info = {}
            
            # Extract basic fields using regex
            fields_to_extract = [
                ('id', r'"id":(\d+)'),
                ('market_name', r'"market_name":"([^"]+)"'),
                ('type', r'"type":"([^"]+)"'),
                ('market_value', r'"market_value":(\d+)'),
                ('suggested_price', r'"suggested_price":(\d+)'),
                ('purchase_price', r'"purchase_price":(\d+)'),
                ('above_recommended_price', r'"above_recommended_price":([\d.-]+)'),
                ('wear', r'"wear":([\d.]+)'),
                ('wear_name', r'"wear_name":"([^"]+)"'),
                ('published_at', r'"published_at":"([^"]+)"'),
                ('preview_id', r'"preview_id":"([^"]+)"'),
                ('name_color', r'"name_color":"([^"]+)"'),
                ('is_commodity', r'"is_commodity":(true|false)'),
                ('price_is_unreliable', r'"price_is_unreliable":(true|false)')
            ]
            
            for field, pattern in fields_to_extract:
                field_match = re.search(pattern, match)
                if field_match:
                    value = field_match.group(1)
                    if field in ['id', 'market_value', 'suggested_price', 'purchase_price']:
                        item_info[field] = int(value)
                    elif field in ['above_recommended_price', 'wear']:
                        item_info[field] = float(value)
                    elif field in ['is_commodity', 'price_is_unreliable']:
                        item_info[field] = value == 'true'
                    else:
                        item_info[field] = value
            
            # Extract item_search fields
            category_match = re.search(r'"category":"([^"]+)"', match)
            if category_match:
                item_info['category'] = category_match.group(1)
            
            sub_type_match = re.search(r'"sub_type":"([^"]+)"', match)
            if sub_type_match:
                item_info['sub_type'] = sub_type_match.group(1)
            
            rarity_match = re.search(r'"rarity":"([^"]+)"', match)
            if rarity_match:
                item_info['rarity'] = rarity_match.group(1)
            
            if item_info:
                items.append(item_info)
                
        except Exception as e:
            print(f"Error extracting item info: {e}")
            continue
    
    return items

def parse_robust_websocket_data(filename):
    """Parse WebSocket data with robust JSON handling"""
    conn = sqlite3.connect('csgoempire_enhanced.db')
    cursor = conn.cursor()
    
    items_processed = 0
    auctions_processed = 0
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                payload = data['payload']
                timestamp = data['t']
                chrome_timestamp = float(data['t'].split('chrome_ts=')[1].split(')')[0]) if 'chrome_ts=' in data['t'] else None
                
                # Parse new items with robust extraction
                if 'new_item' in payload:
                    items = extract_item_info_from_payload(payload)
                    
                    for item in items:
                        if 'id' not in item:
                            continue
                            
                        item_id = item['id']
                        
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
                            item.get('category'),
                            item.get('sub_type'),
                            item.get('rarity'),
                            item.get('wear_name'),
                            item.get('wear'),
                            item.get('market_value'),
                            item.get('suggested_price'),
                            item.get('purchase_price'),
                            item.get('above_recommended_price'),
                            None,  # icon_url - skip for now
                            item.get('preview_id'),
                            item.get('name_color'),
                            item.get('is_commodity', 0),
                            item.get('price_is_unreliable', 0),
                            item.get('published_at')
                        ))
                        
                        items_processed += 1
                        if items_processed % 10 == 0:
                            print(f"Processed {items_processed} items...")
                
                # Parse auction updates (these are usually well-formed)
                elif 'auction_update' in payload:
                    auction_match = re.search(r'"auction_update",\[(.*?)\]', payload)
                    if auction_match:
                        try:
                            auction_data = json.loads('[' + auction_match.group(1) + ']')
                            
                            for auction in auction_data:
                                auction_id = auction['id']
                                
                                # Insert auction if not exists
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
                                
                                auctions_processed += 1
                                
                        except json.JSONDecodeError:
                            # Skip malformed auction data
                            continue
                
            except Exception as e:
                if line_num % 100 == 0:  # Only print every 100th error
                    print(f"Error parsing line {line_num}: {e}")
                continue
    
    conn.commit()
    conn.close()
    print(f"Enhanced WebSocket data imported successfully!")
    print(f"Items processed: {items_processed}")
    print(f"Auction updates processed: {auctions_processed}")

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
        WHERE market_value IS NOT NULL
        ORDER BY market_value DESC
        LIMIT 10
    ''')
    
    print("\nMost Expensive Items:")
    for row in cursor.fetchall():
        print(f"  {row[0]} - ${row[1]:,} ({row[2]}, {row[3]})")
    
    # Show items by type
    cursor.execute('''
        SELECT type, COUNT(*) as count, AVG(market_value) as avg_value
        FROM items 
        WHERE type IS NOT NULL
        GROUP BY type
        ORDER BY avg_value DESC
        LIMIT 10
    ''')
    
    print("\nItems by Type (by average value):")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} items, avg value: ${row[2]:,.0f}")
    
    # Show recent item listings
    cursor.execute('''
        SELECT market_name, market_value, published_at
        FROM items 
        WHERE published_at IS NOT NULL
        ORDER BY published_at DESC
        LIMIT 10
    ''')
    
    print("\nRecent Item Listings:")
    for row in cursor.fetchall():
        print(f"  {row[0]} - ${row[1]:,} ({row[2][:19]})")
    
    conn.close()

if __name__ == "__main__":
    create_enhanced_database()
    parse_robust_websocket_data("csgoempire_websocket_data.jsonl")
    show_item_analysis()
