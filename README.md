# TimeToConvert

A tiny web app that shows a simple green/amber/red signal indicating whether it's a good time to convert one currency to another based on recent historical rates.

- Signal logic: compares the latest FX rate against the 50th and 75th percentiles of the last 180 days.
  - green: latest >= 75th percentile (rate is relatively high → better to convert base→target now)
  - amber: 50th <= latest < 75th percentile
  - red: latest < 50th percentile

This is not financial advice—just a simple historical heuristic.

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

- Data source: exchangerate.host (free, no API key required)
- Currencies: ISO 4217 codes (e.g., USD, EUR, GBP, JPY)
