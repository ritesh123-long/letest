import os
import requests
import pytz
from datetime import datetime
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from telegram import Bot
import google.generativeai as genai

# ===== ENV =====
BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
CHANNEL_ID = os.getenv("TG_CHANNEL_ID")   # @letestRe
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TMDB_API_KEY = os.getenv("TMDB_API_KEY")

# ===== SETUP =====
bot = Bot(token=BOT_TOKEN)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

IST = pytz.timezone("Asia/Kolkata")
app = Flask(__name__)
scheduler = BackgroundScheduler(timezone=IST)

# ===== FETCH DATA =====
def fetch_latest():
    url = f"https://api.themoviedb.org/3/trending/all/day?api_key={TMDB_API_KEY}&language=en-US"
    r = requests.get(url, timeout=15).json()
    return r.get("results", [])[:1]

# ===== GEMINI =====
def generate_caption(title, overview):
    prompt = f"""
Create a Telegram post in BOTH Hindi and English.

Title: {title}
Story: {overview}

Hindi first, then English.
Short and clean.
"""
    return model.generate_content(prompt).text.strip()

# ===== POST =====
def post_daily():
    try:
        data = fetch_latest()
        if not data:
            return

        item = data[0]
        title = item.get("title") or item.get("name", "New Release")
        overview = item.get("overview", "Latest trending release.")

        caption = generate_caption(title, overview)

        msg = f"""
🎬 Latest Release Update

{caption}

#Latest #OTT #Hindi #English
"""
        bot.send_message(chat_id=CHANNEL_ID, text=msg)
        print("✅ Posted to channel")

    except Exception as e:
        print("❌ Error:", e)

# ===== ROUTES =====
@app.route("/")
def home():
    return "Bot is running ✅"

@app.route("/test")
def test_post():
    post_daily()
    return "Test post sent to Telegram ✅"

# ===== START =====
if __name__ == "__main__":
    scheduler.add_job(post_daily, "cron", hour=9, minute=0)
    scheduler.start()

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
