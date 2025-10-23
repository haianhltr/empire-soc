#!/usr/bin/env python3
"""
dashboard.py
Real-time dashboard for CSGOEmpire monitoring
"""

import sqlite3
import time
import os
from datetime import datetime, timedelta

def show_dashboard():
    """Show real-time dashboard"""
    conn = sqlite3.connect('csgoempire_monitor.db')
    cursor = conn.cursor()
    
    while True:
        # Clear screen
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("=" * 100)
        print("🎮 CSGOEmpire Real-Time Monitor Dashboard")
        print("=" * 100)
        print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Recent items with full details
        cursor.execute('''
            SELECT market_name, market_value, type, wear_name, published_at
            FROM items 
            ORDER BY published_at DESC
            LIMIT 8
        ''')
        
        print("🆕 RECENT ITEMS LISTED")
        print("-" * 100)
        recent_items = cursor.fetchall()
        if recent_items:
            for row in recent_items:
                print(f"📦 {row[0]} - ${row[1]:,} ({row[2]}, {row[3]}) - {row[4][:19]}")
        else:
            print("No recent items found")
        
        print()
        
        # Active auctions with item names
        cursor.execute('''
            SELECT i.market_name, a.auction_id, COUNT(au.id) as update_count,
                   MAX(au.highest_bid) as current_bid, MAX(au.number_of_bids) as total_bids,
                   MAX(au.timestamp) as last_update
            FROM items i
            JOIN auctions a ON i.item_id = a.auction_id
            JOIN auction_updates au ON a.auction_id = au.auction_id
            WHERE au.timestamp > datetime('now', '-10 minutes')
            GROUP BY a.auction_id
            ORDER BY update_count DESC
            LIMIT 6
        ''')
        
        print("🔥 ACTIVE AUCTIONS (Last 10 minutes)")
        print("-" * 100)
        active_auctions = cursor.fetchall()
        if active_auctions:
            for row in active_auctions:
                print(f"⚔️  {row[0]} (Auction {row[1]})")
                print(f"   💰 Current: ${row[3]:,} | 📊 {row[4]} total bids | 🔄 {row[2]} updates | ⏰ {row[5][:19]}")
                print()
        else:
            print("No active auctions in the last 10 minutes")
        
        print()
        
        # Top bidders
        cursor.execute('''
            SELECT bidder_id, total_bids, total_spent, last_seen
            FROM bidders 
            ORDER BY total_bids DESC
            LIMIT 6
        ''')
        
        print("👑 TOP BIDDERS")
        print("-" * 100)
        top_bidders = cursor.fetchall()
        if top_bidders:
            for row in top_bidders:
                avg_bid = row[2] / row[1] if row[1] > 0 else 0
                print(f"🎯 Bidder {row[0]}: {row[1]} bids, ${row[2]:,} spent (avg: ${avg_bid:.0f})")
        else:
            print("No bidder data available")
        
        print()
        
        # Market stats
        cursor.execute('SELECT COUNT(*) FROM items')
        total_items = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM auction_updates WHERE timestamp > datetime("now", "-1 hour")')
        recent_updates = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(DISTINCT auction_id) FROM auction_updates WHERE timestamp > datetime("now", "-1 hour")')
        active_auctions_count = cursor.fetchone()[0]
        
        print("📊 MARKET STATS (Last Hour)")
        print("-" * 100)
        print(f"📦 Total items tracked: {total_items}")
        print(f"🔄 Auction updates: {recent_updates}")
        print(f"⚔️  Active auctions: {active_auctions_count}")
        
        print()
        print("Press Ctrl+C to exit, or wait for next update...")
        
        conn.close()
        time.sleep(30)

if __name__ == "__main__":
    try:
        show_dashboard()
    except KeyboardInterrupt:
        print("\nDashboard stopped.")