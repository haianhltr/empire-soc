#!/usr/bin/env python3
"""
CSGOEmpire Monitor - Version 2 (GUI) - ENHANCED DATABASE
Tracks all item snapshots and state changes
"""

import tkinter as tk
from tkinter import scrolledtext, ttk
import subprocess
import time
import threading
import sqlite3
import json
import re
import requests
from datetime import datetime
from websocket import create_connection, WebSocketException
import sys

class CSGOEmpireMonitorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CSGOEmpire Monitor v2 - Enhanced")
        self.root.geometry("900x650")
        self.root.resizable(True, True)
        
        # State variables
        self.chrome_process = None
        self.monitor_thread = None
        self.is_monitoring = False
        self.is_ready = False
        
        # Config
        self.chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        self.user_data = r"C:\Users\haian\AppData\Local\Google\Chrome\User Data"
        self.profile = "Default"
        self.port = 9222
        self.url = "https://csgoempire.com/withdraw/steam/market"

        # Price values from API are already in USD cents, just need to divide by 100
        # No conversion needed - values are stored as cents

        # Setup log file
        self.setup_log_file()

        self.setup_ui()
        self.setup_database()

        # Auto-check for existing Chrome instance on startup
        self.root.after(500, self.auto_detect_chrome)
        
    def setup_ui(self):
        """Setup the user interface"""
        # Status Frame
        status_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        status_frame.pack(fill=tk.X, padx=10, pady=10)
        status_frame.pack_propagate(False)
        
        # Status Label
        self.status_label = tk.Label(
            status_frame,
            text="● NOT READY",
            font=("Arial", 16, "bold"),
            fg="#e74c3c",
            bg="#2c3e50"
        )
        self.status_label.pack(pady=10)
        
        # Status Details
        self.status_detail = tk.Label(
            status_frame,
            text="Click 'Launch Chrome' to begin",
            font=("Arial", 10),
            fg="#ecf0f1",
            bg="#2c3e50"
        )
        self.status_detail.pack()
        
        # Control Frame
        control_frame = tk.Frame(self.root)
        control_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Launch Chrome Button
        self.launch_btn = tk.Button(
            control_frame,
            text="🚀 Launch Chrome",
            font=("Arial", 12, "bold"),
            bg="#3498db",
            fg="white",
            width=20,
            height=2,
            command=self.launch_chrome
        )
        self.launch_btn.pack(side=tk.LEFT, padx=5)
        
        # Start Tracking Button
        self.start_btn = tk.Button(
            control_frame,
            text="▶ Start Tracking",
            font=("Arial", 12, "bold"),
            bg="#27ae60",
            fg="white",
            width=20,
            height=2,
            state=tk.DISABLED,
            command=self.start_tracking
        )
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        # Stop Tracking Button
        self.stop_btn = tk.Button(
            control_frame,
            text="⏸ Stop Tracking",
            font=("Arial", 12, "bold"),
            bg="#e74c3c",
            fg="white",
            width=20,
            height=2,
            state=tk.DISABLED,
            command=self.stop_tracking
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # Stats Frame
        stats_frame = tk.Frame(self.root, bg="#34495e")
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.items_label = tk.Label(
            stats_frame,
            text="Items: 0",
            font=("Arial", 10, "bold"),
            fg="white",
            bg="#34495e"
        )
        self.items_label.pack(side=tk.LEFT, padx=20, pady=5)
        
        self.snapshots_label = tk.Label(
            stats_frame,
            text="Snapshots: 0",
            font=("Arial", 10, "bold"),
            fg="white",
            bg="#34495e"
        )
        self.snapshots_label.pack(side=tk.LEFT, padx=20, pady=5)
        
        self.auctions_label = tk.Label(
            stats_frame,
            text="Auctions: 0",
            font=("Arial", 10, "bold"),
            fg="white",
            bg="#34495e"
        )
        self.auctions_label.pack(side=tk.LEFT, padx=20, pady=5)
        
        # Log Frame with Tabs
        log_frame = tk.LabelFrame(self.root, text="Activity Logs", font=("Arial", 10, "bold"))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Create notebook (tabbed interface)
        from tkinter import ttk
        self.log_notebook = ttk.Notebook(log_frame)
        self.log_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Processed Log Tab
        processed_frame = tk.Frame(self.log_notebook)
        self.log_notebook.add(processed_frame, text="📊 Processed Events")

        # Control frame for processed log
        processed_control_frame = tk.Frame(processed_frame)
        processed_control_frame.pack(fill=tk.X, padx=5, pady=5)

        self.save_processed_log = tk.BooleanVar(value=True)
        save_processed_checkbox = tk.Checkbutton(
            processed_control_frame,
            text="💾 Save to tracker.log",
            variable=self.save_processed_log,
            font=("Arial", 9)
        )
        save_processed_checkbox.pack(side=tk.LEFT)

        self.log_text = scrolledtext.ScrolledText(
            processed_frame,
            wrap=tk.WORD,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#00ff00",
            insertbackground="white"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        # Raw Log Tab
        raw_frame = tk.Frame(self.log_notebook)
        self.log_notebook.add(raw_frame, text="🔍 Raw Messages")

        # Control frame for raw log options
        raw_control_frame = tk.Frame(raw_frame)
        raw_control_frame.pack(fill=tk.X, padx=5, pady=5)

        # First row - format and save options
        raw_row1 = tk.Frame(raw_control_frame)
        raw_row1.pack(fill=tk.X, pady=2)

        self.format_raw = tk.BooleanVar(value=True)
        format_checkbox = tk.Checkbutton(
            raw_row1,
            text="📋 Format for readability",
            variable=self.format_raw,
            font=("Arial", 9)
        )
        format_checkbox.pack(side=tk.LEFT, padx=5)

        self.save_raw_log = tk.BooleanVar(value=True)
        save_raw_checkbox = tk.Checkbutton(
            raw_row1,
            text="💾 Save to raw_tracker.log",
            variable=self.save_raw_log,
            font=("Arial", 9)
        )
        save_raw_checkbox.pack(side=tk.LEFT, padx=5)

        # Second row - filters
        raw_row2 = tk.Frame(raw_control_frame)
        raw_row2.pack(fill=tk.X, pady=2)

        tk.Label(raw_row2, text="Filters:", font=("Arial", 9, "bold")).pack(side=tk.LEFT, padx=5)

        self.filter_new_item = tk.BooleanVar(value=True)
        tk.Checkbutton(raw_row2, text="🆕 New Item", variable=self.filter_new_item, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        self.filter_auction_update = tk.BooleanVar(value=True)
        tk.Checkbutton(raw_row2, text="⚔️ Auction Update", variable=self.filter_auction_update, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        self.filter_deleted_item = tk.BooleanVar(value=True)
        tk.Checkbutton(raw_row2, text="🗑️ Deleted Item", variable=self.filter_deleted_item, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        self.filter_seller_status = tk.BooleanVar(value=True)
        tk.Checkbutton(raw_row2, text="👤 Seller Status", variable=self.filter_seller_status, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        self.filter_other = tk.BooleanVar(value=True)
        tk.Checkbutton(raw_row2, text="❓ Other", variable=self.filter_other, font=("Arial", 8)).pack(side=tk.LEFT, padx=2)

        self.raw_log_text = scrolledtext.ScrolledText(
            raw_frame,
            wrap=tk.WORD,
            font=("Consolas", 8),
            bg="#1e1e1e",
            fg="#ffaa00",
            insertbackground="white"
        )
        self.raw_log_text.pack(fill=tk.BOTH, expand=True)
        
    def setup_database(self):
        """Create enhanced database schema for snapshot tracking"""
        conn = sqlite3.connect('csgoempire_monitor.db')
        cursor = conn.cursor()
        
        # Items master table - one row per unique item ID
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            item_id INTEGER PRIMARY KEY,
            market_name TEXT,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_snapshots INTEGER DEFAULT 0,
            deleted_at TIMESTAMP DEFAULT NULL
        )
        ''')
        
        # Item snapshots - every state change
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            snapshot_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Item details
            market_name TEXT,
            market_value INTEGER,
            suggested_price INTEGER,
            purchase_price INTEGER,
            above_recommended_price REAL,
            
            -- Item classification
            type TEXT,
            category TEXT,
            sub_type TEXT,
            rarity TEXT,
            
            -- Wear info
            wear REAL,
            wear_name TEXT,
            
            -- Auction state
            auction_ends_at INTEGER,
            auction_highest_bid INTEGER,
            auction_highest_bidder INTEGER,
            auction_number_of_bids INTEGER,
            
            -- Seller info
            seller_online_status INTEGER,
            seller_delivery_rate_recent REAL,
            seller_delivery_rate_long REAL,
            seller_delivery_time_recent INTEGER,
            seller_delivery_time_long INTEGER,
            seller_steam_level_min INTEGER,
            seller_steam_level_max INTEGER,
            
            -- Other
            published_at TEXT,
            is_commodity INTEGER,
            price_is_unreliable INTEGER,
            
            FOREIGN KEY (item_id) REFERENCES items(item_id)
        )
        ''')
        
        # Auction updates - real-time bidding activity
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS auction_updates (
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
        
        # Bidders - track bidder activity
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS bidders (
            bidder_id INTEGER PRIMARY KEY,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_bids INTEGER DEFAULT 0,
            highest_bid INTEGER DEFAULT 0,
            total_spent INTEGER DEFAULT 0
        )
        ''')
        
        # Deleted items - track when items are removed with sale type classification
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS deleted_items (
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
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_item_id ON item_snapshots(item_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_time ON item_snapshots(snapshot_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_snapshots_market_name ON item_snapshots(market_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_auction_updates_item_id ON auction_updates(item_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_auction_updates_time ON auction_updates(update_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_items_market_name ON items(market_name)')
        
        conn.commit()
        conn.close()
        self.log("✓ Enhanced database initialized with snapshot tracking")
        self.log("  - items: Master item registry")
        self.log("  - item_snapshots: Every state change")
        self.log("  - auction_updates: Real-time bids")
        self.log("  - bidders: Bidder profiles")
        self.log("  - deleted_items: Sale type tracking (auction_sold/auction_expired/delisted)")
        
    def setup_log_file(self):
        """Setup log file for persistent logging"""
        from datetime import datetime
        import os

        # Use a single log file that appends on every run
        log_filename = "tracker.log"
        self.log_file = open(log_filename, 'a', encoding='utf-8')
        self.log_filename = log_filename

        # Setup raw log file
        raw_log_filename = "raw_tracker.log"
        self.raw_log_file = open(raw_log_filename, 'a', encoding='utf-8')
        self.raw_log_filename = raw_log_filename

        # Write session header
        session_start = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        self.log_file.write(f"\n{'='*80}\n")
        self.log_file.write(f"SESSION STARTED: {session_start}\n")
        self.log_file.write(f"{'='*80}\n")
        self.log_file.flush()

        self.raw_log_file.write(f"\n{'='*80}\n")
        self.raw_log_file.write(f"RAW SESSION STARTED: {session_start}\n")
        self.raw_log_file.write(f"{'='*80}\n")
        self.raw_log_file.flush()

    def log(self, message):
        """Add message to processed log with smart auto-scroll and file logging"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"

        # Write to file only if enabled
        if self.save_processed_log.get():
            try:
                self.log_file.write(log_line + "\n")
                self.log_file.flush()  # Ensure it's written immediately
            except:
                pass

        # Check if user is at the bottom before adding new message
        at_bottom = self.log_text.yview()[1] >= 0.99

        self.log_text.insert(tk.END, log_line + "\n")

        # Only auto-scroll if user was at the bottom
        if at_bottom:
            self.log_text.see(tk.END)

        self.root.update_idletasks()

    def log_raw(self, event_type, payload):
        """Add raw WebSocket message to raw log"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        # Check filters - skip display if filter is off for this type
        should_display = False
        if event_type == "NEW_ITEM" and self.filter_new_item.get():
            should_display = True
        elif event_type == "AUCTION_UPDATE" and self.filter_auction_update.get():
            should_display = True
        elif event_type == "DELETED_ITEM" and self.filter_deleted_item.get():
            should_display = True
        elif event_type == "SELLER_STATUS" and self.filter_seller_status.get():
            should_display = True
        elif event_type == "UNKNOWN" and self.filter_other.get():
            should_display = True

        # Check if we should format for readability
        if self.format_raw.get():
            log_line = self.format_readable(event_type, payload, timestamp)
        else:
            # Show full raw JSON
            try:
                import json
                if payload.startswith('42'):
                    # Socket.IO format - extract the JSON part
                    json_part = payload.split(',', 1)[1] if ',' in payload else payload
                    data = json.loads(json_part)
                    formatted = json.dumps(data, indent=2)
                    log_line = f"[{timestamp}] {event_type}:\n{formatted}\n{'-'*80}\n"
                else:
                    log_line = f"[{timestamp}] {event_type}:\n{payload}\n{'-'*80}\n"
            except:
                log_line = f"[{timestamp}] {event_type}:\n{payload}\n{'-'*80}\n"

        # Write to raw log file (always save, regardless of filters - filters are display-only)
        if self.save_raw_log.get():
            try:
                self.raw_log_file.write(log_line)
                self.raw_log_file.flush()
            except:
                pass

        # Display only if filter allows
        if should_display:
            # Check if user is at the bottom
            at_bottom = self.raw_log_text.yview()[1] >= 0.99

            self.raw_log_text.insert(tk.END, log_line)

            # Only auto-scroll if user was at the bottom
            if at_bottom:
                self.raw_log_text.see(tk.END)

            self.root.update_idletasks()

    def format_readable(self, event_type, payload, timestamp):
        """Format raw message into readable format showing key info"""
        try:
            if event_type == "NEW_ITEM":
                return self.format_new_item(payload, timestamp)
            elif event_type == "AUCTION_UPDATE":
                return self.format_auction_update(payload, timestamp)
            elif event_type == "DELETED_ITEM":
                return self.format_deleted_item(payload, timestamp)
            else:
                return f"[{timestamp}] {event_type}: {payload[:200]}...\n{'-'*80}\n"
        except Exception as e:
            return f"[{timestamp}] {event_type} (format error: {e}):\n{payload[:200]}...\n{'-'*80}\n"

    def format_new_item(self, payload, timestamp):
        """Format new_item message for readability"""
        try:
            # Extract key fields
            import re

            id_match = re.search(r'"id":(\d+)', payload)
            name_match = re.search(r'"market_name":"([^"]+)"', payload)
            price_match = re.search(r'"purchase_price":(\d+)', payload)
            market_val_match = re.search(r'"market_value":(\d+)', payload)
            suggested_match = re.search(r'"suggested_price":(\d+)', payload)
            above_match = re.search(r'"above_recommended_price":([\d.-]+)', payload)
            wear_match = re.search(r'"wear":([\d.]+)', payload)
            wear_name_match = re.search(r'"wear_name":"([^"]+)"', payload)
            auction_match = re.search(r'"auction_ends_at":(\d+|null)', payload)

            # Seller stats
            online_match = re.search(r'"user_online_status":(\d+)', payload)
            delivery_recent_match = re.search(r'"delivery_rate_recent":([\d.]+)', payload)
            delivery_long_match = re.search(r'"delivery_rate_long":([\d.]+)', payload)
            instant_avail_match = re.search(r'"instant_deposit_available_amount":(\d+)', payload)
            instant_max_match = re.search(r'"instant_deposit_max_amount":(\d+)', payload)

            item_id = id_match.group(1) if id_match else "?"
            name = name_match.group(1) if name_match else "Unknown"
            price = int(price_match.group(1)) / 100.0 if price_match else 0
            market_val = int(market_val_match.group(1)) / 100.0 if market_val_match else 0
            suggested = int(suggested_match.group(1)) / 100.0 if suggested_match else 0
            above = float(above_match.group(1)) if above_match else 0
            wear = float(wear_match.group(1)) if wear_match else None
            wear_name = wear_name_match.group(1) if wear_name_match else ""
            is_auction = auction_match.group(1) != 'null' if auction_match else False

            online = int(online_match.group(1)) if online_match else 0
            delivery_recent = float(delivery_recent_match.group(1)) if delivery_recent_match else 0
            delivery_long = float(delivery_long_match.group(1)) if delivery_long_match else 0
            instant_avail = int(instant_avail_match.group(1)) if instant_avail_match else 0
            instant_max = int(instant_max_match.group(1)) if instant_max_match else 0

            # Build formatted output
            lines = [
                f"[{timestamp}] ══════════════════════════════════════════════════════════════",
                f"🆕 NEW ITEM",
                f"├─ ID: {item_id}",
                f"├─ Name: {name}",
                f"├─ Wear: {wear_name} ({wear:.4f})" if wear else f"├─ Wear: {wear_name}",
                f"├─ Type: {'🔨 AUCTION' if is_auction else '💰 FIXED PRICE'}",
                f"├─ Pricing:",
                f"│  ├─ Purchase: ${price:,.2f}",
                f"│  ├─ Market Value: ${market_val:,.2f}",
                f"│  ├─ Suggested: ${suggested:,.2f}",
                f"│  └─ Above Recommended: {above:+.2f}%",
                f"├─ Seller:",
                f"│  ├─ Online: {'🟢 YES' if online == 1 else '🔴 NO'}",
                f"│  ├─ Delivery Rate: {delivery_recent:.0%} (recent) / {delivery_long:.0%} (long)",
                f"│  └─ Instant Deposit: {instant_avail}/{instant_max}",
                f"└─────────────────────────────────────────────────────────────────",
                ""
            ]

            return "\n".join(lines)

        except Exception as e:
            return f"[{timestamp}] NEW_ITEM (parse error: {e}):\n{payload[:200]}...\n{'-'*80}\n"

    def format_auction_update(self, payload, timestamp):
        """Format auction_update message for readability"""
        # Placeholder for now
        return f"[{timestamp}] AUCTION_UPDATE:\n{payload[:200]}...\n{'-'*80}\n"

    def format_deleted_item(self, payload, timestamp):
        """Format deleted_item message for readability"""
        # Placeholder for now
        return f"[{timestamp}] DELETED_ITEM:\n{payload[:200]}...\n{'-'*80}\n"
        
    def update_status(self, ready, detail):
        """Update status display"""
        self.is_ready = ready
        if ready:
            self.status_label.config(text="● READY", fg="#27ae60")
            self.start_btn.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="● NOT READY", fg="#e74c3c")
            self.start_btn.config(state=tk.DISABLED)
        self.status_detail.config(text=detail)
        self.root.update_idletasks()
        
    def check_chrome_running(self):
        """Check if Chrome DevTools is already running"""
        try:
            response = requests.get(f"http://127.0.0.1:{self.port}/json", timeout=2)
            tabs = response.json()
            return True, len(tabs)
        except:
            return False, 0

    def auto_detect_chrome(self):
        """Auto-detect existing Chrome instance on startup"""
        is_running, tab_count = self.check_chrome_running()

        if is_running:
            self.log(f"✓ Detected existing Chrome instance (port {self.port})")
            self.log(f"  Found {tab_count} tab(s)")
            self.update_status(True, "Chrome already running - ready to track")
            self.launch_btn.config(text="🔄 Relaunch Chrome")
        else:
            self.log("No Chrome instance detected")
            self.log("Click 'Launch Chrome' to begin")

    def launch_chrome(self):
        """Launch Chrome with debugging enabled or detect existing instance"""
        self.launch_btn.config(state=tk.DISABLED)

        def run_launcher():
            try:
                # First check if Chrome is already running with debugging
                self.log("Checking for existing Chrome instance...")
                is_running, tab_count = self.check_chrome_running()

                if is_running:
                    self.log(f"✓ Chrome already running with DevTools on port {self.port}")
                    self.log(f"  Found {tab_count} tab(s)")
                    self.log("  Skipping launch - using existing instance")
                    self.update_status(True, "Ready to start tracking (existing Chrome)")
                    return

                self.log("No existing Chrome instance found")
                self.log("Launching Chrome using PowerShell script...")

                # Run the PowerShell launcher script
                result = subprocess.run(
                    ["powershell.exe", "-ExecutionPolicy", "Bypass", "-File", "launch_chrome.ps1"],
                    capture_output=True,
                    text=True,
                    timeout=45
                )

                # Log the output
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self.log(line.strip())

                if result.returncode == 0:
                    self.log("✓ Chrome launched successfully!")
                    self.update_status(True, "Ready to start tracking")
                else:
                    self.log("✗ Chrome launch failed")
                    self.log("Errors:")
                    for line in result.stderr.split('\n'):
                        if line.strip():
                            self.log(f"  {line.strip()}")
                    self.update_status(False, "Failed to launch Chrome")
                    self.launch_btn.config(state=tk.NORMAL)

            except subprocess.TimeoutExpired:
                self.log("✗ Launch timeout (45 seconds)")
                self.update_status(False, "Launch timeout")
                self.launch_btn.config(state=tk.NORMAL)
            except Exception as e:
                self.log(f"✗ Error: {e}")
                self.update_status(False, f"Error: {e}")
                self.launch_btn.config(state=tk.NORMAL)

        # Run in background thread
        threading.Thread(target=run_launcher, daemon=True).start()
    
    def start_tracking(self):
        """Start WebSocket monitoring"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_label.config(text="● TRACKING", fg="#f39c12")
        self.status_detail.config(text="Monitoring WebSocket traffic...")
        
        self.log("=" * 50)
        self.log("Starting WebSocket monitor...")
        
        self.monitor_thread = threading.Thread(target=self.monitor_websocket, daemon=True)
        self.monitor_thread.start()
    
    def stop_tracking(self):
        """Stop WebSocket monitoring"""
        self.is_monitoring = False
        self.stop_btn.config(state=tk.DISABLED)
        self.start_btn.config(state=tk.NORMAL)
        self.status_label.config(text="● READY", fg="#27ae60")
        self.status_detail.config(text="Tracking stopped")
        self.log("Tracking stopped by user")
        
    def monitor_websocket(self):
        """Monitor WebSocket traffic"""
        try:
            # Get WebSocket URL
            self.log("Fetching Chrome tabs...")
            response = requests.get(f"http://127.0.0.1:{self.port}/json", timeout=5)
            tabs = response.json()
            
            self.log(f"Found {len(tabs)} tab(s), looking for CSGOEmpire...")
            
            ws_url = None
            for tab in tabs:
                tab_url = tab.get("url", "").lower()
                if "csgoempire" in tab_url:
                    ws_url = tab.get("webSocketDebuggerUrl")
                    self.log(f"✓ Found CSGOEmpire tab: {tab.get('title', 'Untitled')}")
                    self.log(f"  URL: {tab.get('url', 'Unknown')}")
                    break
            
            if not ws_url:
                self.log("✗ No CSGOEmpire tab found - make sure the page is loaded")
                self.stop_tracking()
                return
            
            self.log(f"Connecting to Chrome DevTools Protocol...")
            
            # Connect to CDP
            cdp = create_connection(ws_url, timeout=10)
            
            # Enable Network domain
            cdp.send(json.dumps({"id": 1, "method": "Network.enable"}))
            
            self.log("✓ Monitoring started - capturing all snapshots...")
            self.log("=" * 50)
            
            message_count = 0
            while self.is_monitoring:
                raw = cdp.recv()
                if not raw:
                    continue

                try:
                    msg = json.loads(raw)
                except:
                    continue

                method = msg.get("method")
                if method == "Network.webSocketFrameReceived":
                    params = msg.get("params", {})
                    frame = params.get("response", {})
                    payload = frame.get("payloadData", "")

                    if payload:
                        message_count += 1
                        # Log first message to confirm we're receiving data
                        if message_count == 1:
                            self.log("✓ Receiving WebSocket messages...")

                        # Determine event type for raw log
                        if '"new_item"' in payload:
                            event_type = "NEW_ITEM"
                        elif '"auction_update"' in payload:
                            event_type = "AUCTION_UPDATE"
                        elif '"deleted_item"' in payload:
                            event_type = "DELETED_ITEM"
                        elif '"updated_seller_online_status"' in payload:
                            event_type = "SELLER_STATUS"
                        else:
                            event_type = "UNKNOWN"

                        # Log raw message
                        self.log_raw(event_type, payload)

                        # Process the message
                        self.process_message(payload)
            
            cdp.close()
            self.log("WebSocket connection closed")
            
        except Exception as e:
            self.log(f"✗ Monitor error: {type(e).__name__}: {e}")
            self.stop_tracking()
    
    def process_message(self, payload):
        """Process WebSocket message and store snapshots"""
        conn = sqlite3.connect('csgoempire_monitor.db')
        cursor = conn.cursor()
        
        try:
            # NEW ITEM - Create full snapshot
            if '"new_item"' in payload:
                # Extract all available fields
                id_match = re.search(r'"id":(\d+)', payload)
                
                if id_match:
                    item_id = int(id_match.group(1))
                    
                    # Register item in master table
                    name_match = re.search(r'"market_name":"([^"]+)"', payload)
                    market_name = name_match.group(1) if name_match else None
                    
                    cursor.execute('''
                        INSERT INTO items (item_id, market_name, total_snapshots)
                        VALUES (?, ?, 1)
                        ON CONFLICT(item_id) DO UPDATE SET
                            market_name = COALESCE(excluded.market_name, market_name),
                            last_seen = CURRENT_TIMESTAMP,
                            total_snapshots = total_snapshots + 1
                    ''', (item_id, market_name))
                    
                    # Create snapshot with ALL fields
                    cursor.execute('''
                        INSERT INTO item_snapshots (
                            item_id, market_name, market_value, suggested_price, purchase_price,
                            above_recommended_price, type, category, sub_type, rarity,
                            wear, wear_name, auction_ends_at, auction_highest_bid,
                            auction_highest_bidder, auction_number_of_bids,
                            seller_online_status, seller_delivery_rate_recent, seller_delivery_rate_long,
                            seller_delivery_time_recent, seller_delivery_time_long,
                            seller_steam_level_min, seller_steam_level_max,
                            published_at, is_commodity, price_is_unreliable
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item_id,
                        market_name,
                        int(re.search(r'"market_value":(\d+)', payload).group(1)) if re.search(r'"market_value":(\d+)', payload) else None,
                        int(re.search(r'"suggested_price":(\d+)', payload).group(1)) if re.search(r'"suggested_price":(\d+)', payload) else None,
                        int(re.search(r'"purchase_price":(\d+)', payload).group(1)) if re.search(r'"purchase_price":(\d+)', payload) else None,
                        float(re.search(r'"above_recommended_price":([\d.-]+)', payload).group(1)) if re.search(r'"above_recommended_price":([\d.-]+)', payload) else None,
                        re.search(r'"type":"([^"]+)"', payload).group(1) if re.search(r'"type":"([^"]+)"', payload) else None,
                        re.search(r'"category":"([^"]+)"', payload).group(1) if re.search(r'"category":"([^"]+)"', payload) else None,
                        re.search(r'"sub_type":"([^"]+)"', payload).group(1) if re.search(r'"sub_type":"([^"]+)"', payload) else None,
                        re.search(r'"rarity":"([^"]+)"', payload).group(1) if re.search(r'"rarity":"([^"]+)"', payload) else None,
                        float(re.search(r'"wear":([\d.]+)', payload).group(1)) if re.search(r'"wear":([\d.]+)', payload) else None,
                        re.search(r'"wear_name":"([^"]+)"', payload).group(1) if re.search(r'"wear_name":"([^"]+)"', payload) else None,
                        int(re.search(r'"auction_ends_at":(\d+)', payload).group(1)) if re.search(r'"auction_ends_at":(\d+)', payload) else None,
                        int(re.search(r'"auction_highest_bid":(\d+)', payload).group(1)) if re.search(r'"auction_highest_bid":(\d+)', payload) else None,
                        int(re.search(r'"auction_highest_bidder":(\d+)', payload).group(1)) if re.search(r'"auction_highest_bidder":(\d+)', payload) else None,
                        int(re.search(r'"auction_number_of_bids":(\d+)', payload).group(1)) if re.search(r'"auction_number_of_bids":(\d+)', payload) else None,
                        int(re.search(r'"user_online_status":(\d+)', payload).group(1)) if re.search(r'"user_online_status":(\d+)', payload) else None,
                        float(re.search(r'"delivery_rate_recent":([\d.]+)', payload).group(1)) if re.search(r'"delivery_rate_recent":([\d.]+)', payload) else None,
                        float(re.search(r'"delivery_rate_long":([\d.]+)', payload).group(1)) if re.search(r'"delivery_rate_long":([\d.]+)', payload) else None,
                        int(re.search(r'"delivery_time_minutes_recent":(\d+)', payload).group(1)) if re.search(r'"delivery_time_minutes_recent":(\d+)', payload) else None,
                        int(re.search(r'"delivery_time_minutes_long":(\d+)', payload).group(1)) if re.search(r'"delivery_time_minutes_long":(\d+)', payload) else None,
                        int(re.search(r'"steam_level_min_range":(\d+)', payload).group(1)) if re.search(r'"steam_level_min_range":(\d+)', payload) else None,
                        int(re.search(r'"steam_level_max_range":(\d+)', payload).group(1)) if re.search(r'"steam_level_max_range":(\d+)', payload) else None,
                        re.search(r'"published_at":"([^"]+)"', payload).group(1) if re.search(r'"published_at":"([^"]+)"', payload) else None,
                        1 if re.search(r'"is_commodity":true', payload) else 0,
                        1 if re.search(r'"price_is_unreliable":true', payload) else 0
                    ))
                    
                    conn.commit()

                    if market_name:
                        value_cents = int(re.search(r'"market_value":(\d+)', payload).group(1)) if re.search(r'"market_value":(\d+)', payload) else 0
                        value_usd = value_cents / 100.0
                        self.log(f"📦 {market_name} - ${value_usd:,.2f} (ID: {item_id})")
                    else:
                        self.log(f"📦 Item ID: {item_id}")

                    self.update_stats()
            
            # AUCTION UPDATE - Track bid changes
            elif '"auction_update"' in payload:
                auction_match = re.search(
                    r'"id":(\d+).*?"auction_highest_bid":(\d+).*?"auction_highest_bidder":(\d+).*?"auction_number_of_bids":(\d+)',
                    payload
                )
                if auction_match:
                    auction_id = int(auction_match.group(1))
                    bid = int(auction_match.group(2))
                    bidder = int(auction_match.group(3))
                    num_bids = int(auction_match.group(4))
                    
                    # Extract additional fields
                    above_match = re.search(r'"above_recommended_price":([\d.-]+)', payload)
                    ends_match = re.search(r'"auction_ends_at":(\d+)', payload)

                    # Try to get item name from database
                    cursor.execute('SELECT market_name FROM items WHERE item_id = ?', (auction_id,))
                    result = cursor.fetchone()
                    item_name = result[0] if result and result[0] else None

                    # Insert auction update
                    cursor.execute('''
                        INSERT INTO auction_updates
                        (auction_id, item_id, market_name, highest_bid, highest_bidder, number_of_bids,
                         above_recommended_price, ends_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        auction_id,
                        auction_id,  # Auction ID = Item ID
                        item_name,   # Store market name if available
                        bid,
                        bidder,
                        num_bids,
                        float(above_match.group(1)) if above_match else None,
                        int(ends_match.group(1)) if ends_match else None
                    ))

                    # Update/create bidder
                    cursor.execute('''
                        INSERT INTO bidders (bidder_id, total_bids, highest_bid)
                        VALUES (?, 1, ?)
                        ON CONFLICT(bidder_id) DO UPDATE SET
                            total_bids = total_bids + 1,
                            highest_bid = MAX(highest_bid, excluded.highest_bid),
                            total_spent = total_spent + excluded.highest_bid,
                            last_seen = CURRENT_TIMESTAMP
                    ''', (bidder, bid))

                    conn.commit()

                    # Use item name for logging
                    display_name = item_name if item_name else f"Item #{auction_id}"

                    bid_usd = bid / 100.0
                    self.log(f"⚔️  {display_name}: ${bid_usd:,.2f} by #{bidder} ({num_bids} bids)")
                    self.update_stats()
            
            # DELETED ITEM - Track removal with sale type classification
            elif '"deleted_item"' in payload:
                deleted_match = re.findall(r'\d{6,}', payload)  # Find all item IDs
                for item_id_str in deleted_match:
                    item_id = int(item_id_str)

                    # Check if item had auction updates (bids)
                    cursor.execute('''
                        SELECT
                            COUNT(*) as bid_count,
                            MAX(highest_bid) as final_bid,
                            MAX(highest_bidder) as final_bidder
                        FROM auction_updates
                        WHERE auction_id = ?
                    ''', (item_id,))

                    auction_data = cursor.fetchone()
                    bid_count = auction_data[0] if auction_data else 0
                    final_bid = auction_data[1] if auction_data and auction_data[1] else None
                    final_bidder = auction_data[2] if auction_data and auction_data[2] else None

                    # Get original listing info
                    cursor.execute('''
                        SELECT auction_ends_at, purchase_price
                        FROM item_snapshots
                        WHERE item_id = ?
                        ORDER BY snapshot_time ASC
                        LIMIT 1
                    ''', (item_id,))

                    listing_data = cursor.fetchone()
                    original_price = listing_data[1] if listing_data else None

                    # Determine if it was an auction:
                    # 1. If we have snapshot data, check auction_ends_at
                    # 2. If no snapshot but has auction_updates, it's an auction
                    if listing_data and listing_data[0] is not None:
                        was_auction = 1  # Has auction_ends_at in snapshot
                    elif bid_count > 0:
                        was_auction = 1  # Has bids = must be auction
                    else:
                        was_auction = 0  # No snapshot, no bids = assume fixed price

                    # Determine sale type based on logic
                    if was_auction:
                        if bid_count > 0:
                            sale_type = 'auction_sold'
                            icon = '🔨'
                        else:
                            sale_type = 'auction_expired'
                            icon = '⏱️'
                    else:
                        # Fixed price item deleted - seller delisted it
                        sale_type = 'delisted'
                        icon = '❌'

                    # Insert with classification
                    cursor.execute('''
                        INSERT INTO deleted_items (
                            item_id, sale_type, had_bids, final_bid_count,
                            final_bid_amount, final_bidder, was_auction, original_price
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        item_id,
                        sale_type,
                        1 if bid_count > 0 else 0,
                        bid_count,
                        final_bid,
                        final_bidder,
                        was_auction,
                        original_price
                    ))

                    # Update items table
                    cursor.execute('''
                        UPDATE items
                        SET deleted_at = CURRENT_TIMESTAMP
                        WHERE item_id = ?
                    ''', (item_id,))

                    # Get item name for logging
                    cursor.execute('SELECT market_name FROM items WHERE item_id = ?', (item_id,))
                    result = cursor.fetchone()
                    item_name = result[0] if result and result[0] else None

                    # Log with sale type
                    if sale_type == 'auction_sold':
                        # Always log auction sales (even without name) - important event
                        display_name = item_name if item_name else f"Item #{item_id}"
                        final_bid_usd = final_bid / 100.0
                        self.log(f"{icon} {display_name} - AUCTION SOLD (${final_bid_usd:,.2f} - {bid_count} bids) [ID: {item_id}]")
                    elif sale_type == 'auction_expired':
                        # Only log if we have the item name
                        if item_name:
                            self.log(f"{icon} {item_name} - AUCTION EXPIRED (no bids) [ID: {item_id}]")
                    else:
                        # For delisted items, only log if we have the item name
                        if item_name:
                            if original_price:
                                price_usd = original_price / 100.0
                                price_str = f" (${price_usd:,.2f})"
                            else:
                                price_str = ""
                            self.log(f"{icon} {item_name}{price_str} - DELISTED [ID: {item_id}]")
                        # Skip logging items without names (not tracked from the start)

                conn.commit()
                self.update_stats()
        
        except Exception as e:
            self.log(f"Error processing: {e}")
        
        finally:
            conn.close()
    
    def update_stats(self):
        """Update statistics display"""
        try:
            conn = sqlite3.connect('csgoempire_monitor.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM items')
            items_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM item_snapshots')
            snapshots_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM auction_updates')
            auctions_count = cursor.fetchone()[0]
            
            conn.close()
            
            self.items_label.config(text=f"Items: {items_count}")
            self.snapshots_label.config(text=f"Snapshots: {snapshots_count}")
            self.auctions_label.config(text=f"Auctions: {auctions_count}")
        except Exception as e:
            pass

if __name__ == "__main__":
    # Fix encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout.reconfigure(encoding='utf-8')

    root = tk.Tk()
    app = CSGOEmpireMonitorGUI(root)

    # Close log files when app closes
    def on_closing():
        try:
            session_end = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            app.log_file.write(f"SESSION ENDED: {session_end}\n")
            app.log_file.write(f"{'='*80}\n\n")
            app.log_file.close()

            app.raw_log_file.write(f"RAW SESSION ENDED: {session_end}\n")
            app.raw_log_file.write(f"{'='*80}\n\n")
            app.raw_log_file.close()
        except:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
