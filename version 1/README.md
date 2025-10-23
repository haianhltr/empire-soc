# CSGOEmpire WebSocket Monitor - Complete Setup
# ================================================

## 🎯 What This Does
Captures real-time WebSocket data from CSGOEmpire marketplace including:
- ✅ **Item names** (e.g., "★ Bayonet | Tiger Tooth (Factory New)")
- ✅ **Auction bidding** (real-time bid updates)
- ✅ **Bidder profiles** (who's bidding, how much they spend)
- ✅ **Market trends** (price movements, item listings)

## 📁 Files Included
- `csgoempire_monitor.py` - Main monitoring script
- `start_monitor.ps1` - PowerShell launcher (Windows)
- `dashboard.py` - Real-time dashboard viewer
- `query_database.py` - Database analysis tool

## 🚀 Quick Start

### 1. Start Monitoring
```powershell
.\start_monitor.ps1
```

### 2. View Dashboard (in another terminal)
```bash
python dashboard.py
```

### 3. Query Database
```bash
python query_database.py
```

## 📊 What You'll See

### Real-time Output:
```
[NEW ITEM] ★ Bayonet | Tiger Tooth (Factory New) - $57,604
[AUCTION] 336616814: $307 by 767490 (40 bids)
[NEW ITEM] ★ Bayonet | Lore (Field-Tested) - $50,403
```

### Dashboard Shows:
- 🆕 Recent items listed with names and prices
- 🔥 Active auctions with item names
- 👑 Top bidders and their spending
- 📊 Market statistics

### Database Queries:
- Items by category (Knives, Gloves, Weapons)
- Most expensive items tracked
- Most active auctions
- Bidder behavior analysis

## 🎮 Example Item Names Captured:
- "★ Bayonet | Tiger Tooth (Factory New)"
- "★ Bayonet | Lore (Field-Tested)" 
- "★ Classic Knife | Scorched (Field-Tested)"
- "★ Moto Gloves | Blood Pressure (Well-Worn)"

## 🔧 Requirements
- Python 3.7+
- Chrome browser
- Windows PowerShell (for launcher script)

## 📈 Database Schema
- **items**: Item names, types, prices, wear conditions
- **auctions**: Auction metadata linked to items
- **auction_updates**: Real-time bid updates
- **bidders**: Bidder profiles and spending stats

## 🎯 Use Cases
- Track specific item prices
- Monitor bidding patterns
- Analyze market trends
- Identify active bidders
- Price alert systems

## ⚡ Performance
- Captures 100+ messages per minute
- Stores item names and full details
- Real-time dashboard updates every 30 seconds
- SQLite database for fast queries

---
**Ready to monitor CSGOEmpire marketplace with full item name detection!** 🎮