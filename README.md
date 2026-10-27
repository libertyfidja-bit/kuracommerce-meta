# KuraCommerce 🛍️
> Built for the Meta Global AI Developer Hackathon (Indie Developer Track: Build for Your World)

## Problem Statement
Informal artisans, tailor shops, and young micro-merchants across Rwanda lack access to design studios, product photography, and multilingual copywriting tools to sell effectively online.

## Solution
KuraCommerce is an automated pipeline that converts raw smartphone snapshots into digital catalog listings:
1. **SAM 3.1**: Extracts and isolates items from noisy, low-light shop backgrounds.
2. **Muse Wonder**: Analyzes visual traits to generate fair pricing estimates (RWF) and ad copy in English and Kinyarwanda.

## Repository Structure
* `backend/app.py`: Flask application server and webhook endpoints.
* `backend/meta_client.py`: Meta Model API integration layer (SAM 3.1, Muse Wonder).
* `backend/requirements.txt`: Python package dependencies.
* `docs/architecture.md`: Pipeline architecture and data flow diagrams.

## Quickstart

### Prerequisites
* Python 3.10+
* Meta Model API Key

### Installation & Run
```bash
# Clone the repository
git clone [https://github.com/your-username/kuracommerce-meta.git](https://github.com/your-username/kuracommerce-meta.git)
cd kuracommerce-meta

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment variables
export META_API_KEY="your-meta-api-key"

# Start the local server
python backend/app.py
