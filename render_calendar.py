# render_calendar.py

import requests
import datetime
from ics import Calendar
from PIL import Image, ImageDraw, ImageFont
import io
import os

import arrow


# Config
CALENDAR_URL = os.getenv("CALENDAR_URL", "https://example.com/your.ics")
IMG_WIDTH, IMG_HEIGHT = 600, 800
OUTPUT_PATH = "output/calendar.png"

# Download calendar
response = requests.get(CALENDAR_URL)
calendar = Calendar(response.text)

# Create blank white image
img = Image.new("L", (IMG_WIDTH, IMG_HEIGHT), 255)
draw = ImageDraw.Draw(img)

# Load font (fallback if not available)
try:
    font = ImageFont.truetype("DejaVuSansMono.ttf", 18)
except:
    font = ImageFont.load_default()

# Header
today = arrow.now().floor('day')
draw.text((20, 10), f"Calendar: {today.strftime('%A, %d %b %Y')}", font=font, fill=0)

# List upcoming events
y = 50
max_events = 10

events = sorted(calendar.timeline.start_after(today))
for event in events[:max_events]:
    start = event.begin.format('ddd DD MMM HH:mm')
    summary = event.name or "(No Title)"
    line = f"{start} - {summary}"
    draw.text((20, y), line, font=font, fill=0)
    y += 30

# Save image
os.makedirs("output", exist_ok=True)
img.save(OUTPUT_PATH)
print(f"Saved image to {OUTPUT_PATH}")
