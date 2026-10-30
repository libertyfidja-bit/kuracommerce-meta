# Contributions: what was built during the hackathon

The hackathon requires the demo to show only features, code and functionality built during
the event, and judges must be able to tell what is new. This file is that record.

> **Fill in every `TODO` yourself and keep only statements that are true.** An inaccurate
> contributions statement is a bigger risk than a small project.

## Event window

- Hackathon start: `TODO (date)`
- Hackathon end: `TODO (date)`
- First commit made during the event: `TODO (commit hash)`
- Last commit before the event, if any: `TODO (commit hash, or "none: repo created during the event")`

If any code existed before the event, tag it so judges can diff against it:

```bash
git tag pre-hackathon <last-pre-event-commit>
git log pre-hackathon..HEAD --stat        # everything added during the event
```

## What was built during the event

Tick only what was truly written during the event window. Remove or relabel the rest.

| Area | Files | Built during event? |
|---|---|---|
| Four-model pipeline (SAM 3.1, Muse Wonder, Muse Image, Muse Spark) with per-step telemetry | `backend/meta_client.py` | `TODO [ ]` |
| Parallel pipeline orchestration, validation, size limits | `backend/app.py` | `TODO [ ]` |
| Persistent listings (SQLite) and public map feed | `backend/storage.py`, `/api/listings` | `TODO [ ]` |
| Server-side admin login and listings table | `backend/app.py`, `templates/index.html` | `TODO [ ]` |
| Trilingual (Kinyarwanda / English / French) campaign and WhatsApp-ready message | `meta_client.py`, `app.py` | `TODO [ ]` |
| Voice-to-item-name input | `templates/index.html` | `TODO [ ]` |
| Map directory with category filters and live listing pins | `templates/index.html` | `TODO [ ]` |
| USSD (*250#) menu simulator | `app.py`, `templates/index.html` | `TODO [ ]` |
| WhatsApp webhook simulator | `app.py` | `TODO [ ]` |
| Automated tests | `backend/test_api.py` | `TODO [ ]` |

## What existed before, or is not ours

Be explicit. Judges expect this section.

- **Open-source libraries:** Flask, Requests, Pillow, python-dotenv, gunicorn, Leaflet, itsdangerous.
- **Map data:** OpenStreetMap tiles.
- **Browser features:** Web Speech API (voice input), Geolocation API.
- **Meta models:** `TODO (list exactly what you ran: for example Muse Glimmer self-hosted from Hugging Face; and/or SAM 3.1, Muse Wonder, Muse Image, Muse Spark through the Meta Model API)`.
- **Organizer confirmation:** open-weight models on self-provided compute are allowed and do not count against us. `TODO: paste the organizers' reply and date here.`
- **Licenses:** Muse Glimmer is Apache 2.0. If you use Muse Spark Open, its license requires showing "Built with Muse Spark Open" in the product's UI.
- **Code that predates the event:** `TODO (list files, or write "none")`

## AI coding assistance

The hackathon encourages the Muse Code coding agent. State what you used it for.

- Tools used: GitHub Codespaces for development. Claude (Anthropic) was used as an AI assistant to review and rewrite parts of the backend, UI and documentation. `TODO: confirm, and add any other tools (for example Muse Code) or correct this line`
- What they helped with: `TODO (for example: error handling, fallback logic, admin authentication, voice-input error handling, tests, documentation)`
- Everything was reviewed and tested by the team: `TODO (yes/no)`

## What the demo shows, and what it does not

Shown, and working:

- Photo and voice in, priced listing and trilingual campaign out, using the Meta models.
- Per-step telemetry showing which model ran and whether the local fallback was used.
- Listings saved on the server and pinned on a shared map.
- Admin dashboard behind server-side login.

Simulated or limited, and labelled that way in the app:

- **USSD:** a simulated menu, not connected to MTN, Airtel or any gateway.
- **WhatsApp:** the app builds the message and opens a `wa.me` link. The webhook is a simulator; it does not call the WhatsApp Cloud API.
- **Map "Sample" pins:** placeholder locations, not real businesses.
- **Fallback mode:** if the Meta API key is missing or a call fails, that step uses a basic local routine and the UI says so.

## Verification for judges

- `GET /api/status` shows whether the Meta API key is configured and which model IDs are used.
- The result card shows each model's name, source (Meta API or local fallback) and latency.
- Admin, View JSON shows the stored telemetry for every listing.
