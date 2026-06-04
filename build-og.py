#!/usr/bin/env python3
"""Generate og.png — 1200x630 link-preview card. One-shot tool, not part of the site build."""
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1200, 630
BG = (234, 237, 224)     # cool sage-tinted paper
FG = (47, 62, 53)        # deep forest ink
MUTED = (86, 100, 89)    # secondary green-grey
ACCENT = (70, 98, 79)    # readable forest-green eyebrow
BORDER = (47, 62, 53)    # hairline (used at low alpha via outline)

img = Image.new("RGB", (W, H), BG)

# subtle atmospheric wash (matches body::before on the site — warm sage glow)
glow = Image.new("RGB", (W, H), BG)
gd = ImageDraw.Draw(glow)
for r, alpha in [(900, -10), (600, -6)]:
    gd.ellipse((W - 360 - r, -220 - r, W - 360 + r, -220 + r),
               fill=(min(255, max(0, BG[0] + alpha - 8)), min(255, max(0, BG[1] + alpha)), min(255, max(0, BG[2] + alpha - 14))))
glow = glow.filter(ImageFilter.GaussianBlur(130))
img = Image.blend(img, glow, 0.55)

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
