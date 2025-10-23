# CSGOEmpire Monitor - Version 2 (GUI)
# =====================================

## 🎯 Simple GUI Application

Version 2 features a **clean, simple GUI** that makes monitoring easy!

## 🚀 Quick Start

Simply run:
```bash
python csgoempire_gui.py
```

## 📱 How to Use

### Step 1: Launch Chrome
- Click **"🚀 Launch Chrome"** button
- Wait for status to change from "NOT READY" to "READY"
- Chrome will open automatically with the CSGOEmpire marketplace

### Step 2: Start Tracking
- Once status shows "● READY"
- Click **"▶ Start Tracking"** button
- Watch real-time data appear in the Activity Log!

### Step 3: Monitor
- See items and auctions in real-time
- Stats update automatically (Items count, Auctions count)
- All data saved to database

### Step 4: Stop
- Click **"⏸ Stop Tracking"** when done
- Data remains saved in the database

## 📊 GUI Features

### Status Indicator
- **● NOT READY** (Red) - Chrome not launched yet
- **● READY** (Green) - Ready to start tracking
- **● TRACKING** (Orange) - Currently monitoring

### Buttons
- **🚀 Launch Chrome** - Starts Chrome with debugging
- **▶ Start Tracking** - Begins WebSocket monitoring
- **⏸ Stop Tracking** - Stops monitoring (keeps data)

### Activity Log
- Real-time display of captured items
- Shows item names and prices
- Shows auction bids as they happen
- Auto-scrolls to latest activity

### Statistics
- **Items:** Total unique items captured
- **Auctions:** Total auction updates tracked

## 📦 What It Captures

```
[10:30:45] 📦 ★ Bayonet | Tiger Tooth (Factory New) - $57,604
[10:30:46] ⚔️  Auction 336616814: $307 by 767490 (40 bids)
[10:30:47] 📦 ★ Classic Knife | Scorched (Field-Tested) - $15,234
[10:30:48] ⚔️  Auction 336616875: $81 by 6073326 (1 bids)
```

## 💾 Database

All data is automatically saved to `csgoempire_monitor.db`:
- **items** table: Item names, values, IDs
- **auction_updates** table: All bid updates

## 🎨 GUI Preview

```
┌─────────────────────────────────────────────────┐
│         CSGOEmpire Monitor v2                   │
├─────────────────────────────────────────────────┤
│                                                 │
│              ● READY                            │
│         Ready to start tracking                 │
│                                                 │
├─────────────────────────────────────────────────┤
│  🚀 Launch Chrome  ▶ Start Tracking  ⏸ Stop   │
├─────────────────────────────────────────────────┤
│  Items: 45        Auctions: 123                │
├─────────────────────────────────────────────────┤
│  Activity Log                                   │
│  ┌───────────────────────────────────────────┐ │
│  │ [10:30:45] 📦 Bayonet | Tiger Tooth...   │ │
│  │ [10:30:46] ⚔️  Auction 336616814: $307   │ │
│  │ [10:30:47] 📦 Classic Knife | Scorched  │ │
│  │                                           │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

## ✨ Improvements from Version 1

- ✅ **No PowerShell needed** - Everything in one Python GUI
- ✅ **Visual status indicators** - See status at a glance
- ✅ **Real-time log display** - Watch captures as they happen
- ✅ **Click to start/stop** - No command line needed
- ✅ **Auto-updates stats** - Live item and auction counts
- ✅ **Clean, simple interface** - Easy to understand

## 🔧 Requirements

- Python 3.7+
- tkinter (usually included with Python)
- websocket-client (`pip install websocket-client`)
- requests (`pip install requests`)

## 💡 Tips

- Keep Chrome window open while tracking
- Don't close the Chrome window manually
- Database persists between sessions
- You can start/stop tracking multiple times

---
**Version 2 - Simple GUI Edition** 🎨
Created: October 23, 2025
