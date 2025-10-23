#!/usr/bin/env python3
"""
query_database.py
Query and analyze the CSGOEmpire database
"""

import sqlite3
from datetime import datetime, timedelta

def query_database():
    """Query database and show analysis"""
    conn = sqlite3.connect('csgoempire_monitor.db')
    cursor = conn.cursor()
    
    print("=" * 80)
    print("CSGOEmpire Database Analysis")
    print("=" * 80)
    print(f"Analysis time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Items by category
    cursor.execute('''
        SELECT category, COUNT(*) as count, AVG(market_value) as avg_value
        FROM items 
        WHERE category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
    ''')
    
    print("📦 ITEMS BY CATEGORY")
    print("-" * 80)
    categories = cursor.fetchall()
    if categories:
        for row in categories:
            print(f"{row[0]}: {row[1]} items, avg value: ${row[2]:,.0f}")
    else:
        print("No category data available")
    
    print()
    
    # Most expensive items
    cursor.execute('''
        SELECT market_name, market_value, type, wear_name, published_at
        FROM items 
        WHERE market_value IS NOT NULL
        ORDER BY market_value DESC
        LIMIT 10
    ''')
    
    print("💰 MOST EXPENSIVE ITEMS")
    print("-" * 80)
    expensive_items = cursor.fetchall()
    if expensive_items:
        for i, row in enumerate(expensive_items, 1):
            print(f"{i:2d}. {row[0]} - ${row[1]:,} ({row[2]}, {row[3]})")
    else:
        print("No item data available")
    
    print()
    
    # Most active auctions
    cursor.execute('''
        SELECT i.market_name, a.auction_id, COUNT(au.id) as update_count,
               MIN(au.highest_bid) as min_bid, MAX(au.highest_bid) as max_bid,
               MAX(au.number_of_bids) as total_bids
        FROM items i
        JOIN auctions a ON i.item_id = a.auction_id
        JOIN auction_updates au ON a.auction_id = au.auction_id
        GROUP BY a.auction_id
        ORDER BY update_count DESC
        LIMIT 10
    ''')
    
    print("🔥 MOST ACTIVE AUCTIONS")
    print("-" * 80)
    active_auctions = cursor.fetchall()
    if active_auctions:
        for i, row in enumerate(active_auctions, 1):
            print(f"{i:2d}. {row[0]} (Auction {row[1]})")
            print(f"    Updates: {row[2]} | Bids: ${row[3]:,} → ${row[4]:,} | Total bids: {row[5]}")
    else:
        print("No auction data available")
    
    print()
    
    # Top bidders
    cursor.execute('''
        SELECT bidder_id, total_bids, total_spent, last_seen
        FROM bidders 
        ORDER BY total_bids DESC
        LIMIT 10
    ''')
    
    print("👑 TOP BIDDERS BY ACTIVITY")
    print("-" * 80)
    top_bidders = cursor.fetchall()
    if top_bidders:
        for i, row in enumerate(top_bidders, 1):
            avg_bid = row[2] / row[1] if row[1] > 0 else 0
            print(f"{i:2d}. Bidder {row[0]}: {row[1]} bids, ${row[2]:,} spent (avg: ${avg_bid:.0f})")
    else:
        print("No bidder data available")
    
    print()
    
    # Recent activity
    cursor.execute('''
        SELECT COUNT(*) FROM auction_updates 
        WHERE timestamp > datetime('now', '-1 hour')
    ''')
    recent_updates = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM items 
        WHERE published_at > datetime('now', '-1 hour')
    ''')
    recent_items = cursor.fetchone()[0]
    
    print("📊 RECENT ACTIVITY (Last Hour)")
    print("-" * 80)
    print(f"Auction updates: {recent_updates}")
    print(f"New items listed: {recent_items}")
    
    conn.close()

def get_item_details(item_name):
    """Get details for a specific item"""
    conn = sqlite3.connect('csgoempire_monitor.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT market_name, market_value, type, wear_name, published_at
        FROM items 
        WHERE market_name LIKE ?
        ORDER BY published_at DESC
        LIMIT 5
    ''', (f'%{item_name}%',))
    
    print(f"\n🔍 SEARCH RESULTS FOR: {item_name}")
    print("-" * 80)
    
    results = cursor.fetchall()
    if results:
        for row in results:
            print(f"📦 {row[0]} - ${row[1]:,} ({row[2]}, {row[3]}) - {row[4][:19]}")
    else:
        print("No items found matching that name")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        get_item_details(sys.argv[1])
    else:
        query_database()
