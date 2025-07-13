import requests
import datetime
import arrow
from ics import Calendar
from PIL import Image, ImageDraw, ImageFont
import io
import os

# Constants
WIDTH, HEIGHT = 800, 600  # Rotate later for Kindle
OUTPUT_PATH = "output/calendar.png"
ICS_URL = os.environ.get("CALENDAR_URL")
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Layout
cols, rows = 3, 3
margin = 20
pad = 12
card_w = (HEIGHT - margin * 2) // cols
card_h = (WIDTH - margin * 2 - 50) // rows

# Fonts
header_big_font = ImageFont.truetype(BOLD_FONT_PATH, 36)
header_small_font = ImageFont.truetype(FONT_PATH, 22)
card_header_font = ImageFont.truetype(BOLD_FONT_PATH, 18)
event_font = ImageFont.truetype(FONT_PATH, 14)
small_font = ImageFont.truetype(FONT_PATH, 12)

# Prepare image
img = Image.new("L", (HEIGHT, WIDTH), 255)
draw = ImageDraw.Draw(img)

# Get Calendar
r = requests.get(ICS_URL)
calendar = Calendar(r.text)

today = arrow.now()
days = [today.shift(days=i).floor('day') for i in range(9)]

# Draw Header
date_text = today.format('dddd, MMMM D')
title_text = "Family Calendar"
w1 = draw.textbbox((0, 0), date_text, font=header_big_font)[2]
w2 = draw.textbbox((0, 0), title_text, font=header_small_font)[2]
draw.text(((HEIGHT - w1) // 2, 10), date_text, font=header_big_font, fill=0)
draw.text(((HEIGHT - w2) // 2, 50), title_text, font=header_small_font, fill=0)

# Cards
for idx, day in enumerate(days):
    col = idx % cols
    row = idx // cols
    x0 = margin + col * card_w
    y0 = 90 + row * card_h
    x1 = x0 + card_w - pad
    y1 = y0 + card_h - pad

    # Gradient Background
    for y in range(y0, y1):
        shade = 230 - int((y - y0) / (y1 - y0) * 50)
        draw.line([(x0, y), (x1, y)], fill=shade)

    # Border
    draw.rounded_rectangle([x0, y0, x1, y1], radius=16, outline=0, width=1)

    # Day Header
    weekday = day.format("ddd").upper()
    date_str = day.format("D MMM")
    draw.text((x0 + 8, y0 + 6), f"{weekday} • {date_str}", font=card_header_font, fill=0)

    # Events
    y_cursor = y0 + 30
    max_lines = 5
    events = sorted(calendar.timeline.on(day.datetime), key=lambda e: e.begin)

    for e in events[:max_lines]:
        if y_cursor + 35 > y1 - 8:
            draw.text((x0 + 10, y_cursor), "...", font=event_font, fill=0)
            break

        # Time
        if e.all_day:
            time_str = "All day"
        else:
            time_str = e.begin.format("HH:mm")

        draw.text((x0 + 10, y_cursor), time_str, font=small_font, fill=80)
        y_cursor += 14

        name = (e.name or "Untitled").strip().replace("\n", " ")[:40]
        draw.text((x0 + 10, y_cursor), name, font=event_font, fill=0)
        y_cursor += 20

# Rotate for Kindle landscape
img = img.rotate(90, expand=True)

# Ensure output dir
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
img.save(OUTPUT_PATH)
