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
ARCHIVO_HERO = _ttf("vendor/fonts/archivo-100-900-latin.woff2", "archivo-hero.ttf", {"wght": 800, "wdth": 118})  # matches the extended site hero
MONO = _ttf("vendor/fonts/martian-mono-300-latin.woff2", "mono.ttf")
ARCHIVO_600 = _ttf("vendor/fonts/archivo-100-900-latin.woff2", "archivo-600.ttf", {"wght": 600, "wdth": 100})

import random

W, H = 1200, 630
PAPER = (250, 247, 243)
INK   = (17, 17, 17)
MUT   = (120, 116, 110)

img = Image.new("RGB", (W, H), PAPER)
draw = ImageDraw.Draw(img)

# faint cold-press grain so it reads as paper, not flat fill
random.seed(7)
px = img.load()
for _ in range(70000):
    x, y = random.randint(0, W - 1), random.randint(0, H - 1)
    r0, g0, b0 = px[x, y]
    d = random.randint(-7, 4)
    px[x, y] = (max(0, r0 + d), max(0, g0 + d), max(0, b0 + d))

# nav pill, centered at top (echoes the live nav)
pill_font = ImageFont.truetype(ARCHIVO_600, 26)
pt = "larsh.dev"
pw = draw.textlength(pt, font=pill_font) + 150
ph = 60
px0 = (W - pw) / 2
py0 = 40
draw.rounded_rectangle((px0, py0, px0 + pw, py0 + ph), radius=18, fill=INK)
draw.text((px0 + 28, py0 + ph / 2), pt, font=pill_font, fill=PAPER, anchor="lm")
chip = ph - 16
draw.rounded_rectangle((px0 + pw - chip - 8, py0 + 8, px0 + pw - 8, py0 + 8 + chip), radius=12, fill=PAPER)

# headline, centered (the hero line) — extended cut to match the site hero
h_font = ImageFont.truetype(ARCHIVO_HERO, 108)
def centered(text, y):
    tw = draw.textlength(text, font=h_font)
    draw.text(((W - tw) / 2, y), text, font=h_font, fill=INK)
    return tw
_w1 = centered("WEB DESIGN", 236)
_w2 = centered("+ FULL STACK", 350)
print(f"headline widths @wdth118/108px: WEB DESIGN={_w1:.0f}, + FULL STACK={_w2:.0f} (card={W}, safe<1120)")

# corner captions, like the hero
cap_font = ImageFont.truetype(ARCHIVO_600, 40)
mono_font = ImageFont.truetype(MONO, 22)
draw.text((64, H - 100), "\u00a92026", font=cap_font, fill=INK)
loc = "MELBOURNE, AUSTRALIA"
lw = draw.textlength(loc, font=mono_font)
draw.text((W - 64 - lw, H - 86), loc, font=mono_font, fill=INK)

img.save("og.png", "PNG", optimize=True)
print("wrote og.png (%dx%d)" % (W, H))
