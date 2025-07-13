import requests
import datetime
import arrow
from ics import Calendar
from PIL import Image, ImageDraw, ImageFont
import io
import os

# Constants
WIDTH, HEIGHT = 800, 600  # Image canvas in portrait (we rotate later)
OUTPUT_PATH = "output/calendar.png"
ICS_URL = os.environ.get("CALENDAR_URL")  # Set in GitHub Secrets

# Fonts
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
header_font = ImageFont.truetype(BOLD_FONT_PATH, 28)
date_font = ImageFont.truetype(BOLD_FONT_PATH, 20)
event_font = ImageFont.truetype(FONT_PATH, 16)

# Create grayscale image
img = Image.new("L", (HEIGHT, WIDTH), 255)
draw = ImageDraw.Draw(img)

# Fetch calendar data
r = requests.get(ICS_URL)
calendar = Calendar(r.text)

# Dates to display
today = arrow.now()
days = [today.shift(days=i) for i in range(6)]  # Keep as Arrow objects

# Draw header
header_text = f"📅 Family Calendar – {today.format('dddd, MMM D')}"
bbox = draw.textbbox((0, 0), header_text, font=header_font)
header_width = bbox[2] - bbox[0]
draw.text(((HEIGHT - header_width) // 2, 20), header_text, font=header_font, fill=0)

# Layout settings
cols = 3
rows = 2
margin = 20
card_w = (HEIGHT - margin * 2) // cols
card_h = (WIDTH - margin * 2 - 50) // rows
pad = 10

# Draw each day's card
for idx, day in enumerate(days):
    col = idx % cols
    row = idx // cols
    x0 = margin + col * card_w
    y0 = 60 + row * card_h
    x1 = x0 + card_w - pad
    y1 = y0 + card_h - pad

    # Card background
    shade = 240 if idx % 2 == 0 else 210
    draw.rounded_rectangle([x0, y0, x1, y1], radius=18, fill=shade)

    # Date header
    weekday = day.format("ddd").upper()
    date_str = day.format("D MMM")
    draw.text((x0 + 12, y0 + 10), f"{weekday} • {date_str}", font=date_font, fill=0)

    # Events
    events = sorted(calendar.timeline.on(day), key=lambda e: e.begin)
    y_cursor = y0 + 40
    max_lines = 6

    for e in events[:max_lines]:
        if y_cursor + 35 > y1 - 10:
            draw.text((x0 + 12, y_cursor), "...", font=event_font, fill=0)
            break

        # Time (smaller & lighter)
        if e.all_day:
            time_str = "📌 All day"
        else:
            time_str = "🕒 " + e.begin.format("HH:mm")
        draw.text((x0 + 12, y_cursor), time_str, font=event_font, fill=100)
        y_cursor += 16

        # Title (bold/dark)
        name = (e.name or "Untitled").strip().replace("\n", " ")[:30]
        draw.text((x0 + 12, y_cursor), name, font=date_font, fill=0)
        y_cursor += 22

# Rotate for Kindle landscape
img = img.rotate(90, expand=True)

# Ensure output dir
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
img.save(OUTPUT_PATH)
