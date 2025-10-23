#!/usr/bin/env python3
"""
Migration Script: Add market_name column to auction_updates table
This adds the column without deleting existing data
"""

import sqlite3
import sys
import os

# Fix encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

db_file = 'csgoempire_monitor.db'

if not os.path.exists(db_file):
    print(f"ERROR - Database not found: {db_file}")
    sys.exit(1)

try:
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    print("Checking current schema...")

    # Check if market_name column already exists
    cursor.execute("PRAGMA table_info(auction_updates)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'market_name' in columns:
        print("✓ Column 'market_name' already exists in auction_updates table")
        conn.close()
        sys.exit(0)

    print("Adding 'market_name' column to auction_updates table...")

    # Add the column
    cursor.execute("ALTER TABLE auction_updates ADD COLUMN market_name TEXT")

    conn.commit()
    print("✓ Migration complete!")
    print("  Column 'market_name' added to auction_updates table")

    # Verify
    cursor.execute("PRAGMA table_info(auction_updates)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"\nUpdated columns: {columns}")

    conn.close()

except Exception as e:
    print(f"✗ Migration failed: {e}")
    sys.exit(1)

print("\nYou can now restart the tracker!")
