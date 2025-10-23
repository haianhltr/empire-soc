# CSGOEmpire WebSocket Monitor - Version 1
# =========================================

## 📦 What's in This Folder

This folder contains **Version 1** of the CSGOEmpire WebSocket monitoring system with full item name detection capabilities.

## 🚀 Main Files (Use These)

### Essential Scripts:
1. **`csgoempire_monitor.py`** - ⭐ Main monitoring script (RECOMMENDED)
2. **`start_monitor.ps1`** - PowerShell launcher for easy startup
3. **`dashboard.py`** - Real-time dashboard viewer
4. **`query_database.py`** - Database analysis and queries

### Legacy Scripts (Original Development):
- `capture_ws_cdp.py` - Original CDP capture script
- `run_ws_capture.ps1` - Original PowerShell launcher

## 🎯 Quick Start

### Method 1: Using the Integrated Monitor (Recommended)
```powershell
.\start_monitor.ps1
```
This will:
1. Close existing Chrome instances
2. Launch Chrome with your profile
3. Start monitoring WebSocket data
4. Save everything to `csgoempire_monitor.db`

### Method 2: Manual Start
```bash
# In one terminal:
python csgoempire_monitor.py

# In another terminal (optional):
python dashboard.py
```

## 📊 What It Captures

✅ **Item Names**: "★ Bayonet | Tiger Tooth (Factory New)"
✅ **Market Values**: Current prices, suggested prices
✅ **Auction Data**: Real-time bidding with bidder IDs
✅ **Item Details**: Type, category, rarity, wear condition
✅ **Bidder Profiles**: Who's bidding and how much they spend

## 🗂️ Database Schema

The system creates `csgoempire_monitor.db` with these tables:
- **items**: Full item details with names, prices, and metadata
- **auctions**: Auction records linked to items
- **auction_updates**: Real-time bid updates
- **bidders**: Bidder profiles and spending statistics

## 📈 Sample Output

```
[NEW ITEM] ★ Bayonet | Tiger Tooth (Factory New) - $57,604
[AUCTION] 336616814: $307 by 767490 (40 bids)
[NEW ITEM] ★ Bayonet | Lore (Field-Tested) - $50,403
[AUCTION] 336616875: $81 by 6073326 (1 bids)
```

## 🔧 Development Files (For Reference)

These files were created during development and testing:
- `complete_csgoempire_monitor.py` - Alternative implementation
- `final_csgoempire_monitor.py` - Another working version
- `create_csgoempire_db.py` - Original database schema
- `enhanced_item_parser.py` - Enhanced parsing logic
- `robust_item_parser.py` - Robust JSON parsing
- `test_extraction.py` - Item extraction tests
- `test_item_extraction.py` - Additional tests

## 📋 Sample Data

- `csgoempire_websocket_data.jsonl` - Sample captured WebSocket data for testing

## 🎮 Use Cases

1. **Track Specific Items**: Monitor prices for items you're interested in
2. **Bidder Analysis**: See who the most active bidders are
3. **Market Trends**: Analyze price movements over time
4. **Price Alerts**: Build alerts for items below certain prices
5. **Auction Activity**: Track which items get the most bids

## 🔄 Upgrading

Future versions will be in separate folders (version 2, version 3, etc.)
This allows you to keep working version 1 while testing new features.

---
**Version 1 - Complete & Working** ✅
Last Updated: October 23, 2025
