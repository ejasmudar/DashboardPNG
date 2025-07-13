import requests
import datetime
import arrow
from ics import Calendar
from PIL import Image, ImageDraw, ImageFont
import io
import os

# Constants
WIDTH, HEIGHT = 800, 600  # Rotate later for landscape
OUTPUT_PATH = "output/calendar.png"
ICS_URL = os.environ.get("ICS_URL", "")  # from secrets
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Create rotated image
img = Image.new("L", (HEIGHT, WIDTH), 255)
draw = ImageDraw.Draw(img)

# Fonts
header_font = ImageFont.truetype(BOLD_FONT_PATH, 28)
date_font = ImageFont.truetype(BOLD_FONT_PATH, 20)  # Event name
event_font = ImageFont.truetype(FONT_PATH, 16)      # Time

# Download ICS
r = requests.get(ICS_URL)
calendar = Calendar(r.text)

# Timeframe
today = arrow.now()
days = [today.shift(days=i).date() for i in range(6)]

# Header
header_text = f"📅 Family Calendar – {today.format('dddd, MMM D')}"
bbox = draw.textbbox((0, 0), header_text, font=header_font)
w = bbox[2] - bbox[0]
draw.text(((HEIGHT - w) // 2, 20), header_text, font=header_font, fill=0)

# Grid layout: 3x2 cards
cols = 3
rows = 2
margin = 20
card_w = (HEIGHT - margin * 2) // cols
card_h = (WIDTH - margin * 2 - 50) // rows
pad = 10

for idx, day in enumerate(days):
    col = idx % cols
    row = idx // cols
    x0 = margin + col * card_w
    y0 = 60 + row * card_h
    x1 = x0 + card_w - pad
    y1 = y0 + card_h - pad

    # Background card
    shade = 240 if idx % 2 == 0 else 210
    draw.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=shade)

    # Header
    weekday = arrow.get(day).format("ddd").upper()
    date_str = arrow.get(day).format("D MMM")
    header = f"{weekday} • {date_str}"
    draw.text((x0 + 12, y0 + 10), header, font=date_font, fill=0)

    # Events
    events = sorted(calendar.timeline.on(day), key=lambda e: e.begin)
    y_cursor = y0 + 40
    max_lines = 6

    for e in events[:max_lines]:
        if y_cursor + 35 > y1 - 10:
            draw.text((x0 + 12, y_cursor), "...", font=event_font, fill=0)
            break

        # Time
        if e.all_day:
            time_str = "📌 All day"
        else:
            time_str = "🕒 " + e.begin.format("HH:mm")
        draw.text((x0 + 12, y_cursor), time_str, font=event_font, fill=100)
        y_cursor += 16

        # Title
        name = e.name or "Untitled"
        name = name.strip().replace("\n", " ")[:30]
        draw.text((x0 + 12, y_cursor), name, font=date_font, fill=0)
        y_cursor += 22

# Rotate for Kindle landscape
img = img.rotate(90, expand=True)

# Ensure output dir
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
img.save(OUTPUT_PATH)
