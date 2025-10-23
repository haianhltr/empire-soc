"""
Database Migration Script
Recreates the database with the new schema
"""

import sqlite3
import os
import sys
import time

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

db_file = 'csgoempire_monitor.db'

# Delete old database if exists
if os.path.exists(db_file):
    print(f"Removing old database: {db_file}")
    try:
        os.remove(db_file)
        print("OK - Old database removed")
    except PermissionError:
        print("ERROR - Database is locked (close GUI first)")
        print("Close the GUI and run this script again")
        sys.exit(1)

# Create new database with enhanced schema
print("Creating new database with enhanced schema...")
conn = sqlite3.connect(db_file)
cursor = conn.cursor()

# Items master table
cursor.execute('''
CREATE TABLE items (
    item_id INTEGER PRIMARY KEY,
    market_name TEXT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_snapshots INTEGER DEFAULT 0,
    deleted_at TIMESTAMP DEFAULT NULL
)
''')

# Item snapshots
cursor.execute('''
CREATE TABLE item_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    market_name TEXT,
    market_value INTEGER,
    suggested_price INTEGER,
    purchase_price INTEGER,
    above_recommended_price REAL,
    
    type TEXT,
    category TEXT,
    sub_type TEXT,
    rarity TEXT,
    
    wear REAL,
    wear_name TEXT,
    
    auction_ends_at INTEGER,
    auction_highest_bid INTEGER,
    auction_highest_bidder INTEGER,
    auction_number_of_bids INTEGER,
    
    seller_online_status INTEGER,
    seller_delivery_rate_recent REAL,
    seller_delivery_rate_long REAL,
    seller_delivery_time_recent INTEGER,
    seller_delivery_time_long INTEGER,
    seller_steam_level_min INTEGER,
    seller_steam_level_max INTEGER,
    
    published_at TEXT,
    is_commodity INTEGER,
    price_is_unreliable INTEGER,
    
    FOREIGN KEY (item_id) REFERENCES items(item_id)
)
''')

# Auction updates
cursor.execute('''
CREATE TABLE auction_updates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    auction_id INTEGER NOT NULL,
    item_id INTEGER,
    market_name TEXT,
    update_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    highest_bid INTEGER,
    highest_bidder INTEGER,
    number_of_bids INTEGER,
    above_recommended_price REAL,
    ends_at INTEGER,

    FOREIGN KEY (item_id) REFERENCES items(item_id)
)
''')

# Bidders
cursor.execute('''
CREATE TABLE bidders (
    bidder_id INTEGER PRIMARY KEY,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_bids INTEGER DEFAULT 0,
    highest_bid INTEGER DEFAULT 0,
    total_spent INTEGER DEFAULT 0
)
''')

# Deleted items with sale type classification
cursor.execute('''
CREATE TABLE deleted_items (
    item_id INTEGER,
    deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Sale classification
    sale_type TEXT,
    had_bids INTEGER DEFAULT 0,
    final_bid_count INTEGER DEFAULT 0,
    final_bid_amount INTEGER DEFAULT NULL,
    final_bidder INTEGER DEFAULT NULL,

    -- Original listing info
    was_auction INTEGER DEFAULT 0,
    original_price INTEGER,

    FOREIGN KEY (item_id) REFERENCES items(item_id)
)
''')

# Create indexes
print("Creating indexes...")
cursor.execute('CREATE INDEX idx_snapshots_item_id ON item_snapshots(item_id)')
cursor.execute('CREATE INDEX idx_snapshots_time ON item_snapshots(snapshot_time)')
cursor.execute('CREATE INDEX idx_snapshots_market_name ON item_snapshots(market_name)')
cursor.execute('CREATE INDEX idx_auction_updates_item_id ON auction_updates(item_id)')
cursor.execute('CREATE INDEX idx_auction_updates_time ON auction_updates(update_time)')
cursor.execute('CREATE INDEX idx_items_market_name ON items(market_name)')

conn.commit()
conn.close()

print("OK - Database created successfully!")
print("\nTables created:")
print("  - items (master registry)")
print("  - item_snapshots (state tracking)")
print("  - auction_updates (bid tracking)")
print("  - bidders (bidder profiles)")
print("  - deleted_items (sale type tracking: auction_sold/auction_expired/delisted)")
print("\nYou can now run: python csgoempire_gui.py")

