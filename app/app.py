import os
from datetime import date, timedelta
from flask import Flask, jsonify, render_template, request, send_from_directory, Response
from io import BytesIO
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


@app.get("/robots.txt")
def robots():
    return send_from_directory(app.static_folder, "robots.txt")


@app.get("/about")
def about():
    return render_template("about.html")


@app.get("/og.png")
def og_image():
    # Generate a simple Open Graph image dynamically (1200x630)
    try:
        from PIL import Image, ImageDraw, ImageFont
        # Inputs (optional) to personalize the image
        base = (request.args.get("base") or "").upper()[:4]
        target = (request.args.get("target") or "").upper()[:4]
        signal = (request.args.get("signal") or "").lower()
        days = request.args.get("days") or ""

        W, H = 1200, 630
        img = Image.new("RGB", (W, H), "#0f172a")
        draw = ImageDraw.Draw(img)

        # Title and subtitle
        title = "Time To Convert"
        if base and target:
            pair = f"{base}→{target}"
        else:
            pair = "Simple FX timing"
        if signal in ("green", "amber", "red"):
            subtitle = f"{pair} — {signal.capitalize()} signal"
        else:
            subtitle = f"{pair} (p50 / p75)"
        if days:
            subtitle += f" • last {days}d"

        # Load a truetype font if available
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        try:
            font_title = ImageFont.truetype(font_path, 72)
            font_sub = ImageFont.truetype(font_path, 36)
        except Exception:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()

        # Centered text
        tw, th = draw.textbbox((0, 0), title, font=font_title)[2:]
        sw, sh = draw.textbbox((0, 0), subtitle, font=font_sub)[2:]
        draw.text(((W - tw) / 2, (H - th) / 2 - 20), title, font=font_title, fill="#e2e8f0")
        draw.text(((W - sw) / 2, (H - sh) / 2 + 60), subtitle, font=font_sub, fill="#94a3b8")

        # Accent circle color based on signal
        color = {
            "green": "#10b981",
            "amber": "#f59e0b",
            "red": "#ef4444",
        }.get(signal, "#10b981")
        r = 18
        cx, cy = 80, 80
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=color)

        bio = BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        return Response(bio.getvalue(), mimetype="image/png")
    except Exception:
        # Fallback: 1x1 transparent PNG
        transparent_png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\x0cIDATx\x9cc``\x00\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        return Response(transparent_png, mimetype="image/png")


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
