# render_calendar.py

import requests
import datetime
from ics import Calendar
from PIL import Image, ImageDraw, ImageFont
import io
import os

import arrow

# Canvas setup (portrait mode first, rotate later)
WIDTH, HEIGHT = 600, 800
MARGIN = 20
GRID_COLS, GRID_ROWS = 3, 2
BOX_W = (WIDTH - 2 * MARGIN) // GRID_COLS
BOX_H = (HEIGHT - MARGIN - 80) // GRID_ROWS  # 80 for header

OUTPUT_PATH = "output/calendar.png"
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
BOLD_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Setup fonts
header_font = ImageFont.truetype(BOLD_FONT_PATH, 28)
date_font = ImageFont.truetype(BOLD_FONT_PATH, 20)
event_font = ImageFont.truetype(FONT_PATH, 16)

# Create canvas
img = Image.new("L", (WIDTH, HEIGHT), color=255)
draw = ImageDraw.Draw(img)

# Header
today = arrow.now()
header_text = f"Family Calendar – {today.format('dddd, MMM D')}"
w, _ = draw.textsize(header_text, font=header_font)
draw.text(((WIDTH - w) // 2, 20), header_text, font=header_font, fill=0)

# Calendar fetch
calendar_url = os.environ.get("CALENDAR_URL")
calendar = Calendar(requests.get(calendar_url).text)

# Create output folder
os.makedirs("output", exist_ok=True)

# Draw each day
for i in range(6):
    day = today.shift(days=i)
    events = list(calendar.timeline.on(day))

    col = i % GRID_COLS
    row = i // GRID_COLS
    x0 = MARGIN + col * BOX_W
    y0 = 80 + row * BOX_H
    x1 = x0 + BOX_W - 10
    y1 = y0 + BOX_H - 10

    # Background card
    bg_color = 230 if i % 2 == 0 else 200  # alternating grey shades
    draw.rounded_rectangle([x0, y0, x1, y1], radius=12, fill=bg_color, outline=80)

    # Date header
    date_str = day.format("ddd, MMM D")
    draw.text((x0 + 10, y0 + 10), date_str, font=date_font, fill=0)

    # Events
    y_cursor = y0 + 35
    max_lines = 5
    for e in events[:max_lines]:
        if e.all_day:
            time_str = "All day"
        else:
            time_str = e.begin.format("HH:mm")
        line = f"{time_str} – {e.name}"
        if y_cursor + 20 > y1 - 10:
            draw.text((x0 + 12, y_cursor), "...", font=event_font, fill=0)
            break
        draw.text((x0 + 12, y_cursor), line[:32], font=event_font, fill=0)
        y_cursor += 20


# Rotate for Kindle landscape
os.makedirs("output", exist_ok=True)
img = img.rotate(90, expand=True)
img.save(OUTPUT_PATH)
