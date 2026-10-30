# KuraCommerce Hub

Photo and voice in, priced trilingual WhatsApp listing out, then pinned on a shared map.
Built for Rwandan micro-merchants (barbers, tailors, market vendors, artisans) for the
**Meta Global AI Developer Hackathon, Build for Your World** track.

Live demo: https://kuracommerce-meta.onrender.com
Contributions and what was built during the event: see [CONTRIBUTIONS.md](CONTRIBUTIONS.md).
Architecture: see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## The problem

Merchants in Kigali sell through WhatsApp and word of mouth, but phone photos look rough,
writing a good ad in Kinyarwanda, English and French takes time, and buyers cannot easily
find nearby sellers.

## Meta models used

| Model | Job |
|---|---|
| SAM 3.1 | Segment the product from its background |
| Muse Wonder | Read the photo and return title, category, description and an RWF price |
| Muse Image | Studio-style enhancement of the photo |
| Muse Spark | Kinyarwanda, English and French promotional copy |

If the API key is missing or a call fails, that step falls back to a basic local routine and
the app says so on screen. `GET /api/status` shows whether the key is configured.

## Running without a Meta API key (open-weight mode)

The organizers confirmed that building on Meta's open-weight models on your own compute is allowed
and not penalised. In this mode one self-hosted **Muse Glimmer** (open weights, Apache 2.0, accepts
text and images) handles the photo analysis and the trilingual ad copy. The SAM and image steps use
a labelled local fallback, because no open-weight equivalent is served. Set the variables in
`.env.example` (Option B). The result card always shows the model id that answered each step.

## Features

- Studio: photo, voice or typed item name, stock count, low-stock alert, `wa.me` order link.
- Map directory (Leaflet and OpenStreetMap): every listing created in the studio is saved and shown to all visitors. "Sample" pins are placeholders.
- Admin: server-side login, saved listings, and per-listing model telemetry.
- USSD (*250#) and WhatsApp webhook: simulators only, not connected to a telecom or the WhatsApp Cloud API.

## Run locally

```bash
cd backend
pip install -r requirements.txt
cp ../.env.example .env        # then set META_API_KEY and ADMIN_PASSWORD
python app.py                  # http://127.0.0.1:5001
python test_api.py             # in another terminal
```

## Deploy on Render

`render.yaml` is included. Set `META_API_KEY` and `ADMIN_PASSWORD` under Environment. Attach a
Disk and set `DB_PATH` (for example `/var/data/kuracommerce.db`) if listings must survive redeploys.

## Known limitations

- Endpoint paths and response shapes in `meta_client.py` must match the current Meta Model API docs.
- Merchant verification checks the phone number format only; it does not verify ownership.
- Free-tier hosting wipes the database on restart unless a Disk is attached.
