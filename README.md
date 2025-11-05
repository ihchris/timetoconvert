# TimeToConvert

A tiny web app that shows a simple green/amber/red signal indicating whether it's a good time to convert one currency to another based on recent historical rates.

- Signal logic: compares the latest FX rate against the 50th and 75th percentiles of the last 180 days.
  - green: latest >= 75th percentile (rate is relatively high → better to convert base→target now)
  - amber: 50th <= latest < 75th percentile
  - red: latest < 50th percentile

This is not financial advice—just a simple historical heuristic.

## Why use this site

- Instant read: you don’t need to interpret charts—the app compares today’s rate with recent history and gives a simple signal.
- Transparent heuristic: uses 50th and 75th percentiles over a configurable lookback (default 180 days).
- Lightweight and free: no login or API key required for basic usage.

## How it works

1. Fetches a timeseries for the chosen pair over the last N days.
2. Computes p50 and p75 percentiles of those rates.
3. Gets the latest rate and classifies:
  - green: latest >= 75th percentile
  - amber: 50th <= latest < 75th percentile
  - red: latest < 50th percentile

Limitations: this is a backward-looking heuristic; markets move and spreads/fees may matter more than small differences in the spot rate.

## Run with Docker

The app is containerized via docker-compose.

- Build and run:

  1. Ensure Docker is running
  2. From the repo root, run:

     docker-compose up --build

  3. Open http://localhost:8000 in your browser

## Environment

No env vars required by default. You can adjust defaults via:

- HISTORY_DAYS (default 180)
- P75_THRESHOLD (default 0.75)
- P50_THRESHOLD (default 0.50)

## Local development (optional)

- Install Python 3.10+
- pip install -r requirements.txt
- FLASK_APP=app.app:app flask run --port 8000

## Notes

- Data source: Frankfurter (https://www.frankfurter.app, free, no API key required)
- Currencies: ISO 4217 codes (e.g., USD, EUR, GBP, JPY)

## SEO / Sharing

- Default meta title/description are included in `templates/index.html`.
- When you check a pair, the page title and description update dynamically (client-side) like “USD→EUR — Green signal | Time To Convert”.
- Social preview image: the app now serves a dynamic Open Graph image at `/og.png` (1200x630) and sets both `og:image` and `twitter:image` automatically with absolute URLs. Twitter card is configured as `summary_large_image`.
- The Docker image installs DejaVu fonts so text renders correctly in the generated image.

## Roadmap ideas

- Alerts when a pair crosses p50/p75 or a custom threshold (email/Slack).
- Longer history options and volatility bands.
- Embeddable widget and simple JSON API.
