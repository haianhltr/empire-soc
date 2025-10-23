# CSGOEmpire WebSocket Data Structure Analysis

## 📊 **Data Overview**

Based on analyzing `csgoempire_websocket_data.jsonl` (1,418 lines):

### **Message Type Distribution:**
1. **`deleted_item`** - 453 messages (32%) - Items removed from marketplace
2. **`new_item`** - 385 messages (27%) - New items listed
3. **`updated_seller_online_status`** - 335 messages (24%) - Seller status updates
4. **`auction_update`** - 175 messages (12%) - Bid updates on auctions
5. **`updated_item`** - 9 messages (<1%) - Item detail changes

---

## 🔍 **Message Structure**

Each line is a JSON object with this wrapper:

```json
{
  "dir": "recv",
  "t": "2025-10-23 03:05:03.535Z (chrome_ts=420068.122079)",
  "requestId": "22328.105",
  "url": "",
  "opcode": 1,
  "payload": "42/trade,[\"event_type\",[{...data...}]]"
}
```

### **Key Fields:**
- `dir`: Direction (`recv` = received from server)
- `t`: Timestamp with Chrome timestamp
- `requestId`: WebSocket connection ID
- `opcode`: 1 = text frame
- `payload`: Socket.IO formatted message

---

## 📦 **1. NEW_ITEM Messages**

**What it captures:** Full details when item is listed

### **Sample Structure:**
```json
42/trade,["new_item",[{
  "id": 336617347,
  "market_name": "★ Bayonet | Tiger Tooth (Factory New)",
  "market_value": 57604,
  "suggested_price": 57552,
  "purchase_price": 57604,
  "above_recommended_price": 0.1,
  "type": "★ Covert Knife",
  "wear": 0.033,
  "wear_name": "Factory New",
  "published_at": "2025-10-23T03:05:04.659708Z",
  
  "item_search": {
    "category": "Weapon",
    "type": "Knife",
    "sub_type": "Bayonet",
    "rarity": "Covert"
  },
  
  "depositor_stats": {
    "delivery_rate_recent": 1,
    "delivery_rate_long": 1,
    "delivery_time_minutes_recent": 0,
    "delivery_time_minutes_long": 1,
    "steam_level_min_range": 61,
    "steam_level_max_range": 99,
    "user_online_status": 1,
    "instant_deposit_available_amount": 0,
    "instant_deposit_max_amount": 7
  },
  
  "auction_ends_at": null,
  "auction_highest_bid": null,
  "auction_highest_bidder": null,
  "auction_number_of_bids": 0,
  
  "icon_url": "...",
  "preview_id": "3c0cb826cc04",
  "name_color": "8650AC",
  "is_commodity": false,
  "price_is_unreliable": false,
  "marketplace_privacy_protection_level": "base",
  "stickers": [],
  "keychains": [],
  "blue_percentage": null,
  "fade_percentage": null
}]]
```

### **Key Insights:**
✅ **Item Identification:**
  - `id` - Unique item ID (same as auction ID)
  - `market_name` - Full item name with skin/wear
  
✅ **Pricing Data:**
  - `market_value` - Current market price
  - `suggested_price` - CSGOEmpire's suggested price
  - `purchase_price` - What seller wants
  - `above_recommended_price` - % above/below suggested (0.1 = +0.1%)

✅ **Item Details:**
  - `type` - Knife/Gloves/Weapon type
  - `wear` - Float value (0.033)
  - `wear_name` - Factory New/Minimal Wear/etc
  - `category`, `sub_type`, `rarity` - Item classification

✅ **Seller Info:**
  - `depositor_stats` - Seller reputation and delivery speed
  - `user_online_status` - 1 = online, 0 = offline
  - `steam_level_min_range` / `max_range` - Seller's Steam level

✅ **Auction State:**
  - Can be null (fixed price) or have auction data
  - `auction_ends_at` - Unix timestamp when auction ends

---

## ⚔️ **2. AUCTION_UPDATE Messages**

**What it captures:** Real-time bidding activity

### **Sample Structure:**
```json
42/trade,["auction_update",[{
  "id": 336616875,
  "above_recommended_price": -4.77,
  "auction_highest_bid": 81,
  "auction_highest_bidder": 6073326,
  "auction_number_of_bids": 1,
  "auction_ends_at": 1761188742
}]]
```

### **Key Insights:**
✅ **Auction ID:**
  - `id` - Links to item ID from `new_item`

✅ **Bid Tracking:**
  - `auction_highest_bid` - Current highest bid amount
  - `auction_highest_bidder` - User ID of highest bidder
  - `auction_number_of_bids` - Total number of bids placed
  - `auction_ends_at` - Unix timestamp

✅ **Price Context:**
  - `above_recommended_price` - % difference from suggested price
  - Negative = below recommended (good deal)
  - Positive = above recommended (overpriced)

---

## 🗑️ **3. DELETED_ITEM Messages**

**What it captures:** Items removed/sold

### **Sample Structure:**
```json
42/trade,["deleted_item",[336617233, 336617238, 336617241]]
```

### **Key Insights:**
✅ **Simple ID List:**
  - Array of item IDs that were removed
  - Could be sold, delisted, or expired

✅ **Use Cases:**
  - Track when items sell
  - Calculate time-to-sale
  - Identify popular items (sell fast)

---

## 👤 **4. UPDATED_SELLER_ONLINE_STATUS Messages**

**What it captures:** Seller availability changes

### **Sample Structure:**
```json
42/trade,["updated_seller_online_status",[
  {"deposit_id": 326659071, "current": 0},
  {"deposit_id": 336486871, "current": 1}
]]
```

### **Key Insights:**
✅ **Status Tracking:**
  - `deposit_id` - Item deposit ID
  - `current` - 1 = seller online, 0 = offline

✅ **Use Cases:**
  - Track seller activity patterns
  - Priority for items with online sellers (faster delivery)

---

## 🔄 **5. UPDATED_ITEM Messages**

**What it captures:** Changes to existing listings (rare)

### **Purpose:**
- Price changes
- Description updates
- Auction modifications

---

## 💡 **Key Relationships**

```
┌─────────────┐
│  new_item   │──┐
│  id: 12345  │  │
└─────────────┘  │
                 │  SAME ID
┌─────────────┐  │
│auction_update│ ←┘
│  id: 12345   │
└─────────────┘

┌─────────────┐
│deleted_item │
│  [12345]    │  ← Item removed/sold
└─────────────┘
```

**Item Lifecycle:**
1. `new_item` - Item listed with full details
2. `auction_update` (0-N times) - Bidding activity
3. `updated_seller_online_status` - Seller status changes
4. `deleted_item` - Item sold or delisted

---

## 📈 **Database Schema Implications**

### **Recommended Tables:**

```sql
items (
  item_id PRIMARY KEY,
  market_name,
  market_value,
  suggested_price,
  purchase_price,
  above_recommended_price,
  type, category, sub_type, rarity,
  wear, wear_name,
  published_at,
  deleted_at  -- From deleted_item
)

auction_updates (
  id AUTOINCREMENT,
  auction_id → items.item_id,
  timestamp,
  highest_bid,
  highest_bidder,
  number_of_bids,
  ends_at
)

bidders (
  bidder_id PRIMARY KEY,
  total_bids,
  highest_bid,
  last_seen
)

seller_status (
  deposit_id → items.item_id,
  timestamp,
  online_status
)
```

---

## 🎯 **What You Can Track**

### **1. Price Discovery**
- Track `above_recommended_price` over time
- Identify overpriced/underpriced items
- Market sentiment analysis

### **2. Bidding Patterns**
- Which items get most bids
- Average bid increments
- Auction duration vs final price

### **3. Seller Behavior**
- Delivery rates from `depositor_stats`
- Online patterns
- Pricing strategies

### **4. Item Lifecycle**
- Time from listing to sale
- Number of bids before sale
- Final sale price vs listing price

### **5. Market Trends**
- Most listed item types
- Popular price ranges
- Fast-selling categories

---

## 🚨 **Important Notes**

1. **ID Linking:** `new_item.id` = `auction_update.id`
2. **Timestamps:** Mix of ISO 8601 and Unix timestamps
3. **Arrays:** `new_item` can contain multiple items
4. **Null Values:** Auction fields null for fixed-price items
5. **Socket.IO Format:** Payload starts with "42/trade,"

---

## 🔥 **High-Value Data Points**

For **sniping deals**:
- `above_recommended_price < -10` (10%+ below market)
- `auction_number_of_bids == 0` (no competition)
- `depositor_stats.delivery_rate_long == 1` (reliable seller)
- `user_online_status == 1` (fast delivery)

For **market analysis**:
- Track `market_value` changes over time
- `deleted_item` timing = sale velocity
- `auction_number_of_bids` = demand indicator

---

**Generated:** October 23, 2025
**Data Source:** 1,418 WebSocket messages captured

