# 🌍 KuraCommerce Hub
**Multimodal AI Commerce Studio, Local Service Finder & Live Map Directory for Rwandan Micro-Merchants**

* **Hackathon**: Meta Global AI Developer Hackathon
* **Track**: Indie Developer — *Build for Your World*
* **Repository**: `https://github.com/libertyfidja-bit/kuracommerce-meta`

---

## 💡 The Problem & Local Impact
Across Kigali and broader Rwanda, thousands of informal micro-merchants, artisans, barbershops, tailors, and fresh market vendors rely on WhatsApp and word-of-mouth to reach customers. However, they face three major barriers:
1. **No Studio Photography**: Phone snapshots taken in busy markets or small shops lack clean lighting and presentation.
2. **Pricing & Copywriting Friction**: Merchants struggle to write high-converting promotional copy across **Kinyarwanda, English, and French**.
3. **Discoverability**: Local buyers often do not know where nearby barbershops, tailors, or market stalls are located or how to book them instantly.

**KuraCommerce Hub** solves all three challenges in a unified web platform powered by Meta's multimodal model suite.

---

## 🤖 Integrated Meta Models (`backend/meta_client.py`)
Our backend pipeline orchestrates four core Meta AI models with automatic local visual inspection fallbacks:
1. **`sam-3.1` (Segment Anything Model 3.1)**: Isolates the foreground product, craft, or storefront subject from cluttered backgrounds.
2. **`muse-wonder`**: Performs multimodal visual inspection, extracts physical image attributes (resolution, lighting, color profile), categorizes the product/service, and suggests fair market pricing in **Rwandan Francs (RWF)**.
3. **`muse-image`**: Enhances isolated product snapshots into studio-ready commercial visuals.
4. **`muse-spark`**: Generates instant, high-converting WhatsApp marketing campaigns in **English, Kinyarwanda, and French**.

---

## ✨ Key Platform Features (3-in-1 Portal)

### 1. Merchant & Service Studio (User View)
* **Strict Merchant Verification**: Requires the seller's real WhatsApp Business number before processing.
* **Multi-Sector Support**: Supports Artisan Crafts, Barber Shops & Hair Salons, Local Markets & Fresh Produce, Fashion & Tailoring, and Electronics Repair.
* **Dynamic Visual Inspection**: Reads the uploaded image's real attributes and generates an accurate visual description, RWF valuation, and trilingual ad campaign.
* **1-Click WhatsApp Ordering & Google Maps Routing**: Buyers can click **"Order / Book Appointment on WhatsApp Now"** or open turn-by-turn directions to the seller's neighborhood.

### 2. Interactive Local Services & Map Directory
* Powered by **Leaflet.js & OpenStreetMap**, centered on key commercial hubs in Kigali (*Kimironko Market, Nyamirambo, Downtown Kigali, Remera Gisimenti, and Nyabugogo*).
* Category filters for **Barber Shops & Salons**, **Local Markets**, and **Crafts & Tailors**.
* Every newly processed listing in Tab 1 is automatically pinned onto the live interactive map in real time.

### 3. Password-Protected Admin Dashboard
* Protected by an administrator authentication gate (Default demo password: `admin123`).
* Logs all merchant submissions, timestamps, WhatsApp contact numbers, neighborhood coordinates, and RWF prices.
* Features an interactive **"🔍 View Order & Telemetry JSON"** modal so judges and system administrators can inspect the complete backend model execution payload.

---

## 📂 Project Architecture

```text
kuracommerce-meta/
├── backend/
│   ├── app.py                 # Flask server, API routes & WhatsApp webhook
│   ├── meta_client.py         # SAM 3.1, Muse Wonder, Muse Image & Muse Spark client
│   ├── requirements.txt       # Pinned Python dependencies (Flask, Requests, Pillow, Dotenv)
│   ├── test_api.py            # Automated CLI test suite for health, studio & webhook routes
│   └── templates/
│       └── index.html         # 3-tab responsive UI (Studio, Leaflet Map, Admin Modal)
├── .env.example               # Template for META_API_KEY configuration
├── .gitignore                 # Protects .env and Python cache files
└── README.md                  # Project documentation