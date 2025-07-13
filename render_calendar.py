# render_calendar.py

import requests
import datetime
from ics import Calendar
from PIL import Image, ImageDraw, ImageFont
import io
import os

import arrow


# Constants
WIDTH, HEIGHT = 600, 800  # Start in portrait mode, rotate later
BOX_W, BOX_H = WIDTH // 4, (HEIGHT - 80) // 2
OUTPUT_PATH = "output/calendar.png"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Use safe fallback

# Create canvas
img = Image.new("L", (WIDTH, HEIGHT), color=255)
draw = ImageDraw.Draw(img)

# Fonts
title_font = ImageFont.truetype(FONT_PATH, 28)
date_font = ImageFont.truetype(FONT_PATH, 18)
event_font = ImageFont.truetype(FONT_PATH, 16)

# Header
today = arrow.now()
header_text = f"Family Calendar – {today.format('dddd, MMM D')}"
draw.text((20, 20), header_text, font=title_font, fill=0)

# Fetch calendar
url = os.environ.get("CALENDAR_URL")
calendar = Calendar(requests.get(url).text)

# Filter next 8 days
for i in range(8):
    day = today.shift(days=i)
    events = list(calendar.timeline.on(day))

    # Box position
    row = i // 4
    col = i % 4
    x0, y0 = col * BOX_W, 80 + row * BOX_H

    # Draw rectangle
    draw.rectangle([x0, y0, x0 + BOX_W, y0 + BOX_H], outline=0)

    # Date header
    date_str = day.format("ddd, MMM D")
    draw.text((x0 + 5, y0 + 5), date_str, font=date_font, fill=0)

    # Events
    y_cursor = y0 + 30
    if events:
        for e in events[:5]:  # limit lines to avoid overflow
            time = e.begin.format("HH:mm") if e.begin else ""
            txt = f"{time} – {e.name}"
            draw.text((x0 + 8, y_cursor), txt[:28], font=event_font, fill=0)
            y_cursor += 20
    else:
        draw.text((x0 + 8, y_cursor), "(No events)", font=event_font, fill=150)

# Rotate for Kindle landscape
img = img.rotate(90, expand=True)
img.save(OUTPUT_PATH)
