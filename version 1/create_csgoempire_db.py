#!/usr/bin/env python3
"""
create_csgoempire_db.py
Create SQLite database schema for CSGOEmpire WebSocket data
"""

import sqlite3
import json
import re
from datetime import datetime

def create_database():
    conn = sqlite3.connect('csgoempire.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS auctions (
        id INTEGER PRIMARY KEY,
        auction_id INTEGER UNIQUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS auction_updates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        auction_id INTEGER,
        timestamp TEXT,
        chrome_timestamp REAL,
        highest_bid INTEGER,
        highest_bidder INTEGER,
        number_of_bids INTEGER,
        ends_at INTEGER,
        above_recommended_price REAL,
        FOREIGN KEY (auction_id) REFERENCES auctions (auction_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER UNIQUE,
        icon_url TEXT,
        blue_percentage REAL,
        fade_percentage REAL,
        auction_ends_at INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
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
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS item_deletions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        timestamp TEXT,
        chrome_timestamp REAL,
        FOREIGN KEY (item_id) REFERENCES items (item_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS seller_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        deposit_id INTEGER,
        timestamp TEXT,
        chrome_timestamp REAL,
        is_online INTEGER,
        FOREIGN KEY (deposit_id) REFERENCES sellers (deposit_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS sellers (
        deposit_id INTEGER PRIMARY KEY,
        first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    
    # Create indexes for better performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_auction_updates_auction_id ON auction_updates (auction_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_auction_updates_timestamp ON auction_updates (timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_item_listings_item_id ON item_listings (item_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_item_deletions_item_id ON item_deletions (item_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_seller_status_deposit_id ON seller_status (deposit_id)')
    
    conn.commit()
    conn.close()
    print("Database schema created successfully!")

def parse_websocket_data(filename):
    """Parse WebSocket data and insert into database"""
    conn = sqlite3.connect('csgoempire.db')
    cursor = conn.cursor()
    
    with open(filename, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            try:
                data = json.loads(line.strip())
                payload = data['payload']
                timestamp = data['t']
                chrome_timestamp = float(data['t'].split('chrome_ts=')[1].split(')')[0]) if 'chrome_ts=' in data['t'] else None
                
                # Parse auction updates
                if 'auction_update' in payload:
                    auction_match = re.search(r'"auction_update",\[(.*?)\]', payload)
                    if auction_match:
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
                
                # Parse new items
                elif 'new_item' in payload:
                    # Extract item data (simplified - would need more parsing for full item details)
                    item_match = re.search(r'"new_item",\[(.*?)\]', payload)
                    if item_match:
                        # For now, just record the timestamp
                        cursor.execute('''
                            INSERT INTO item_listings (item_id, timestamp, chrome_timestamp, auction_ends_at)
                            VALUES (?, ?, ?, ?)
                        ''', (line_num, timestamp, chrome_timestamp, None))
                
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
                
                # Parse seller status updates
                elif 'updated_seller_online_status' in payload:
                    status_match = re.search(r'"updated_seller_online_status",\[(.*?)\]', payload)
                    if status_match:
                        status_data = json.loads('[' + status_match.group(1) + ']')
                        
                        for status in status_data:
                            deposit_id = status['deposit_id']
                            is_online = status['current']
                            
                            # Insert seller if not exists
                            cursor.execute('INSERT OR IGNORE INTO sellers (deposit_id) VALUES (?)', (deposit_id,))
                            
                            # Insert status update
                            cursor.execute('''
                                INSERT INTO seller_status (deposit_id, timestamp, chrome_timestamp, is_online)
                                VALUES (?, ?, ?, ?)
                            ''', (deposit_id, timestamp, chrome_timestamp, is_online))
                            
                            # Update seller last_seen
                            cursor.execute('''
                                UPDATE sellers SET last_seen = CURRENT_TIMESTAMP WHERE deposit_id = ?
                            ''', (deposit_id,))
                
            except Exception as e:
                print(f"Error parsing line {line_num}: {e}")
                continue
    
    conn.commit()
    conn.close()
    print("WebSocket data imported successfully!")

def show_database_stats():
    """Show database statistics"""
    conn = sqlite3.connect('csgoempire.db')
    cursor = conn.cursor()
    
    print("\n=== Database Statistics ===")
    
    # Count records in each table
    tables = ['auctions', 'auction_updates', 'item_listings', 'item_deletions', 'seller_status', 'sellers', 'bidders']
    for table in tables:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        print(f"{table}: {count} records")
    
    # Show top bidders
    print("\n=== Top Bidders ===")
    cursor.execute('''
        SELECT bidder_id, total_bids, total_spent, last_seen
        FROM bidders 
        ORDER BY total_bids DESC 
        LIMIT 10
    ''')
    for row in cursor.fetchall():
        print(f"Bidder {row[0]}: {row[1]} bids, ${row[2]} spent, last seen: {row[3]}")
    
    # Show most active auctions
    print("\n=== Most Active Auctions ===")
    cursor.execute('''
        SELECT a.auction_id, COUNT(au.id) as update_count, 
               MIN(au.highest_bid) as min_bid, MAX(au.highest_bid) as max_bid
        FROM auctions a
        JOIN auction_updates au ON a.auction_id = au.auction_id
        GROUP BY a.auction_id
        ORDER BY update_count DESC
        LIMIT 10
    ''')
    for row in cursor.fetchall():
        print(f"Auction {row[0]}: {row[1]} updates, ${row[2]} → ${row[3]}")
    
    conn.close()

if __name__ == "__main__":
    create_database()
    parse_websocket_data("csgoempire_websocket_data.jsonl")
    show_database_stats()
