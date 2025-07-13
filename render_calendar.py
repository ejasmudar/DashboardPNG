import requests
import datetime
import pytz
from icalendar import Calendar
from dateutil.rrule import rrulestr
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import os
import platform
import random
from io import BytesIO

# --- Config ---
WIDTH, HEIGHT = 800, 600  # Will rotate for Kindle
OUTPUT_PATH = "output/calendar.png"
ICS_URL = os.environ.get("CALENDAR_URL")
DAYS_TO_SHOW = 6
TIMEZONE = pytz.timezone("Asia/Kolkata")

if platform.system() == "Windows":
    FONT_PATH = "C:\\Windows\\Fonts\\arial.ttf"
    BOLD_FONT_PATH = "C:\\Windows\\Fonts\\arialbd.ttf"
else:
    FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    BOLD_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

cols, rows = 3, 2
margin, pad = 20, 12
card_w = (WIDTH - margin * 2) // cols
card_h = (HEIGHT - margin * 2 - 50) // rows


# --- Fonts ---
def load_fonts():
    return {
        "header_big": ImageFont.truetype(BOLD_FONT_PATH, 36),
        "header_small": ImageFont.truetype(FONT_PATH, 22),
        "card_header": ImageFont.truetype(BOLD_FONT_PATH, 18),
        "event": ImageFont.truetype(FONT_PATH, 22),
        "small": ImageFont.truetype(FONT_PATH, 16),
    }


# --- Fetch a random blurred background ---
def get_random_background(width, height):
    try:
        seed = random.randint(10000, 99999)
        url = f"https://picsum.photos/seed/{seed}/{height}/{width}"
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            bg = Image.open(BytesIO(resp.content)).convert("L")
            bg = bg.rotate(90, expand=True)
            bg = bg.filter(ImageFilter.GaussianBlur(radius=4))
            bg = ImageEnhance.Brightness(bg).enhance(0.7)
            return bg.convert("RGBA")
    except Exception as e:
        print("Background load failed:", e)
    return Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))


# --- Parse ICS and return all relevant event instances ---
def get_event_instances(ics_url, start, end, tz):
    calendar = Calendar.from_ical(requests.get(ics_url).text)
    events = []

    for component in calendar.walk():
        if component.name != "VEVENT":
            continue

        summary = str(component.get("SUMMARY", "Untitled"))
        dtstart = component.get("DTSTART").dt
        if isinstance(dtstart, datetime.date) and not isinstance(dtstart, datetime.datetime):
            dtstart = datetime.datetime.combine(dtstart, datetime.time.min).replace(tzinfo=tz)

        rrule_field = component.get("RRULE")
        if rrule_field:
            rrule_str = "RRULE:" + ";".join(f"{k}={','.join(map(str, v))}" for k, v in rrule_field.items())
            rule = rrulestr(rrule_str, dtstart=dtstart)
            for occ in rule.between(start, end, inc=True):
                events.append((occ.astimezone(tz), summary))
        else:
            if start <= dtstart <= end:
                events.append((dtstart.astimezone(tz), summary))

    return events


# --- Create one semi-transparent card with events ---
def draw_event_card(base_img, fonts, day, events, position, idx):
    card_width = card_w - pad
    card_height = card_h - pad
    x0, y0 = position
    darker = idx % 2

    card_img = Image.new("RGBA", (card_width, card_height), (255, 255, 255, 0))
    card_draw = ImageDraw.Draw(card_img)

    fade_limit = int(card_height * 0.85)
    for y in range(card_height):
        if y < fade_limit:
            shade = 230 - darker * 50 + int((y / fade_limit) * 25 * (darker + 2))
        else:
            shade = 255
        alpha = 180  # transparency level
        card_draw.line([(0, y), (card_width, y)], fill=(shade, shade, shade, alpha))

    # Rounded corner mask
    rounded_mask = Image.new("L", (card_width, card_height), 0)
    rounded_draw = ImageDraw.Draw(rounded_mask)
    rounded_draw.rounded_rectangle([(0, 0), (card_width - 1, card_height - 1)], radius=16, fill=255)
    # Apply rounded mask to alpha channel manually with transparency
    final_card = Image.new("RGBA", (card_width, card_height), (0, 0, 0, 0))
    final_card.paste(card_img, (0, 0), rounded_mask)

    # Composite onto base
    base_img.alpha_composite(final_card, dest=(x0, y0))

    # Blend card onto background
    base_img.alpha_composite(card_img, dest=(x0, y0))

    # Draw text on main image
    draw = ImageDraw.Draw(base_img)
    weekday = day.strftime("%a").upper()
    date_str = day.strftime("%-d %b") if platform.system() != "Windows" else day.strftime("%#d %b")
    draw.text((x0 + 10, y0 + 6), f"{weekday} • {date_str}", font=fonts["card_header"], fill=0)

    y_cursor = y0 + 45
    events_today = [(dt, title) for dt, title in events if dt.date() == day.date()]
    events_today.sort()

    for dt, title in events_today:
        if y_cursor + 38 > y0 + card_height - 8:
            draw.text((x0 + 10, y_cursor), "...", font=fonts["event"], fill=0)
            break
        time_str = "All day" if dt.hour == 0 and dt.minute == 0 else dt.strftime("%H:%M")
        draw.text((x0 + 10, y_cursor), time_str, font=fonts["small"], fill=80)
        y_cursor += 16
        name = title.strip().replace("\n", " ")[:40]
        draw.text((x0 + 10, y_cursor), name, font=fonts["event"], fill=0)
        y_cursor += 36


# --- Main composition ---
def generate_calendar_image():
    fonts = load_fonts()
    img = get_random_background(WIDTH, HEIGHT)
    draw = ImageDraw.Draw(img)

    # Header
    now = datetime.datetime.now(TIMEZONE)
    date_text = now.strftime('%A, %B %d')
    title_text = "Family Calendar"
    w1 = draw.textbbox((0, 0), date_text, font=fonts["header_big"])[2]
    w2 = draw.textbbox((0, 0), title_text, font=fonts["header_small"])[2]

    draw.text(((WIDTH - w1) // 2, 10), date_text, font=fonts["header_big"], fill=0, stroke_width=1, stroke_fill=(255, 255, 255, 255))
    draw.text(((WIDTH - w2) // 2, 50), title_text, font=fonts["header_small"], fill=0, stroke_width=1, stroke_fill=(255, 255, 255, 255))

    # Days and events
    days = [now + datetime.timedelta(days=i) for i in range(DAYS_TO_SHOW)]
    end = days[-1] + datetime.timedelta(days=1)
    events = get_event_instances(ICS_URL, now, end, TIMEZONE)

    # Draw cards
    for idx, day in enumerate(days):
        col, row = idx % cols, idx // cols
        x0 = margin + col * card_w
        y0 = 90 + row * card_h
        draw_event_card(img, fonts, day, events, (x0, y0), idx)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    img.save(OUTPUT_PATH)
    print(f"✅ Calendar image saved to {OUTPUT_PATH}")


# --- Run ---
if __name__ == "__main__":
    generate_calendar_image()
