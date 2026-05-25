#!/usr/bin/env python3
"""Generate og.png — 1200x630 link-preview card. One-shot tool, not part of the site build."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1200, 630
BG = (10, 11, 13)
FG = (244, 245, 247)
MUTED = (139, 144, 153)
ACCENT = (76, 143, 255)
BORDER = (36, 38, 43)

img = Image.new("RGB", (W, H), BG)

# subtle atmospheric glow (matches body::before on the site)
glow = Image.new("RGB", (W, H), BG)
gd = ImageDraw.Draw(glow)
for r, alpha in [(900, 18), (600, 12)]:
    gd.ellipse((W - 400 - r, -200 - r, W - 400 + r, -200 + r),
               fill=(min(255, BG[0] + alpha), min(255, BG[1] + alpha + 2), min(255, BG[2] + alpha + 5)))
glow = glow.filter(ImageFilter.GaussianBlur(120))
img = Image.blend(img, glow, 0.6)

draw = ImageDraw.Draw(img)

# circular portrait
portrait = Image.open("assets/portrait.JPG").convert("RGB")
size = 360
pw, ph = portrait.size
s = min(pw, ph)
portrait = portrait.crop(((pw - s) // 2, (ph - s) // 2, (pw + s) // 2, (ph + s) // 2)).resize((size, size), Image.LANCZOS)
mask = Image.new("L", (size, size), 0)
ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
px, py = 95, (H - size) // 2
img.paste(portrait, (px, py), mask)
# hairline ring around portrait
draw.ellipse((px - 1, py - 1, px + size + 1, py + size + 1), outline=BORDER, width=2)

# typography
FONT = "/System/Library/Fonts/HelveticaNeue.ttc"
font_display = ImageFont.truetype(FONT, 64, index=1)  # Bold
font_sub = ImageFont.truetype(FONT, 26, index=0)      # Regular
font_micro = ImageFont.truetype(FONT, 20, index=1)    # Bold

tx = 540

# accent eyebrow
draw.text((tx, 175), "LARSH.DEV", font=font_micro, fill=ACCENT)

# display line (manual wrap)
lines = [
    "I build native apps",
    "and privacy-first",
    "web tools.",
]
y = 210
for line in lines:
    draw.text((tx, y), line, font=font_display, fill=FG)
    y += 72

# byline
draw.text((tx, y + 18), "Lars Holmström  ·  Melbourne", font=font_sub, fill=MUTED)

img.save("og.png", "PNG", optimize=True)
print(f"wrote og.png ({W}x{H})")
