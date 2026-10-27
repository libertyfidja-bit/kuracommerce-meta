# KuraCommerce Architecture & Data Flow

```text
[Phone Camera / WhatsApp Ingest]
              │
              ▼
    [POST /api/process-product]
              │
    ┌─────────┴─────────────────────┐
    ▼                               ▼
[SAM 3.1 via Meta API]     [Muse Wonder via Meta API]
(Masks foreground craft)   (Visual features & pricing)
    │                               │
    └─────────┬─────────────────────┘
              ▼
[Localized Ad Package (EN / Kinyarwanda)]
              │
              ▼
[Merchant Dashboard / WhatsApp Webhook]
