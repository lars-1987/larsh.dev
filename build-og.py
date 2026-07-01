#!/usr/bin/env python3
"""Generate og.png — 1200x630 link-preview card echoing the black hero card.
One-shot tool, not part of the site build. Run: python3 build-og.py"""
import os, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

# decompress self-hosted woff2 -> static ttf so PIL renders the real Archivo / Martian Mono
_tmp = tempfile.mkdtemp()
def _ttf(src, out, axes=None):
    f = TTFont(src)
    if axes:
        instancer.instantiateVariableFont(f, axes, inplace=True)
    f.flavor = None
    p = os.path.join(_tmp, out)
    f.save(p)
    return p
ARCHIVO_800 = _ttf("vendor/fonts/archivo-100-900-latin.woff2", "archivo-800.ttf", {"wght": 800, "wdth": 100})
MONO = _ttf("vendor/fonts/martian-mono-300-latin.woff2", "mono.ttf")

W, H = 1200, 630
PAPER = (242, 236, 223)
CARD  = (14, 13, 12)
FG    = (243, 238, 227)
MUT   = (154, 150, 140)
ACC   = (227, 154, 99)

img = Image.new("RGB", (W, H), PAPER)

# black card inset with padding (mirrors the hero)
m = 40
cw, ch = W - 2*m, H - 2*m
card = Image.new("RGB", (cw, ch), CARD)

# soft peach glow, upper area (echoes the blob)
glow = Image.new("RGB", (cw, ch), CARD)
gd = ImageDraw.Draw(glow)
r = 360
gd.ellipse((cw - 300 - r, -40 - r, cw - 300 + r, -40 + r), fill=(70, 44, 28))
glow = glow.filter(ImageFilter.GaussianBlur(150))
card = Image.blend(card, glow, 0.75)

cd = ImageDraw.Draw(card)
pad = 60
wordmark = ImageFont.truetype(MONO, 22)
h_font = ImageFont.truetype(ARCHIVO_800, 96)
tag_font = ImageFont.truetype(MONO, 20)

# wordmark, top-left (letterspaced)
cd.text((pad, 46), "L A R S   H O L M S T R Ö M", font=wordmark, fill=FG)

# headline bottom-left: "WEB DESIGN +" / "FULL STACK", peach plus
y1, y2 = ch - 250, ch - 150
l1a = "WEB DESIGN "
cd.text((pad, y1), l1a, font=h_font, fill=FG)
w1 = cd.textlength(l1a, font=h_font)
cd.text((pad + w1, y1), "+", font=h_font, fill=ACC)
cd.text((pad, y2), "FULL STACK", font=h_font, fill=FG)

# tagline
cd.text((pad, ch - 62), "Web designer & full-stack developer   ·   Melbourne", font=tag_font, fill=MUT)

# round the card corners and paste onto paper
mask = Image.new("L", (cw, ch), 0)
ImageDraw.Draw(mask).rounded_rectangle((0, 0, cw, ch), radius=36, fill=255)
img.paste(card, (m, m), mask)

img.save("og.png", "PNG", optimize=True)
print("wrote og.png (%dx%d)" % (W, H))
