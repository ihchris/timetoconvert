import os
from datetime import date, timedelta
from flask import Flask, jsonify, render_template, request
import requests

app = Flask(__name__, template_folder="templates", static_folder="static")

HISTORY_DAYS = int(os.getenv("HISTORY_DAYS", "180"))
P75_THRESHOLD = float(os.getenv("P75_THRESHOLD", "0.75"))
P50_THRESHOLD = float(os.getenv("P50_THRESHOLD", "0.50"))

SUPPORTED = [
    "USD","EUR","GBP","JPY","AUD","CAD","CHF","CNY","SEK","NZD","BRL"
]

# Simple currency -> flag emoji mapping for UI selects
FLAGS = {
    "USD": "🇺🇸",
    "EUR": "🇪🇺",
    "GBP": "🇬🇧",
    "JPY": "🇯🇵",
    "AUD": "🇦🇺",
    "CAD": "🇨🇦",
    "CHF": "🇨🇭",
    "CNY": "🇨🇳",
    "SEK": "🇸🇪",
    "NZD": "🇳🇿",
    "BRL": "🇧🇷",
}

# Map currency codes to ISO 3166-1 alpha-2 country/region codes for flag images
FLAG_CODES = {
    "USD": "us",
    "EUR": "eu",
    "GBP": "gb",
    "JPY": "jp",
    "AUD": "au",
    "CAD": "ca",
    "CHF": "ch",
    "CNY": "cn",
    "SEK": "se",
    "NZD": "nz",
    "BRL": "br",
}

# Using Frankfurter (free, no auth): https://www.frankfurter.app/
BASE_URL = "https://api.frankfurter.app"


def fetch_timeseries(base: str, target: str, days: int):
    end = date.today()
    start = end - timedelta(days=days)
    # Frankfurter timeseries pattern: /YYYY-MM-DD..YYYY-MM-DD?from=USD&to=EUR
    url = f"{BASE_URL}/{start.isoformat()}..{end.isoformat()}"
    params = {"from": base, "to": target}
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    rates = []
    for _d, obj in sorted(data.get("rates", {}).items()):
        v = obj.get(target)
        if v is not None:
            rates.append(v)
    return rates


def fetch_latest(base: str, target: str):
    url = f"{BASE_URL}/latest"
    params = {"from": base, "to": target}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    return data.get("rates", {}).get(target)


def percentile(values, p):
    if not values:
        return None
    s = sorted(values)
    k = (len(s) - 1) * p
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[int(k)]
    d0 = s[f] * (c - k)
    d1 = s[c] * (k - f)
    return d0 + d1


def compute_signal(base: str, target: str, history_days: int = HISTORY_DAYS):
    series = fetch_timeseries(base, target, history_days)
    if not series:
        return {"signal": "unknown", "reason": "no_data", "latest": None}
    latest = fetch_latest(base, target)
    if latest is None:
        return {"signal": "unknown", "reason": "no_latest", "latest": None}

    p50 = percentile(series, P50_THRESHOLD)
    p75 = percentile(series, P75_THRESHOLD)

    if latest >= p75:
        signal = "green"
        label = "Great time to convert"
    elif latest >= p50:
        signal = "amber"
        label = "Decent time to convert"
    else:
        signal = "red"
        label = "Probably wait"

    return {
        "signal": signal,
        "label": label,
        "latest": latest,
        "p50": p50,
        "p75": p75,
        "days": history_days,
    }


@app.get("/")
def index():
    return render_template("index.html", supported=SUPPORTED, flags=FLAGS, flag_codes=FLAG_CODES)


@app.get("/api/signal")
def api_signal():
    base = request.args.get("base", "USD").upper()
    target = request.args.get("target", "EUR").upper()
    if base == target:
        return jsonify({"error": "base_target_same"}), 400
    if base not in SUPPORTED or target not in SUPPORTED:
        return jsonify({"error": "unsupported_currency", "supported": SUPPORTED}), 400
    try:
        res = compute_signal(base, target, HISTORY_DAYS)
        return jsonify(res)
    except requests.HTTPError as e:
        return jsonify({"error": "http_error", "detail": str(e)}), 502
    except Exception as e:
        return jsonify({"error": "unknown", "detail": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
