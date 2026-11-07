#!/usr/bin/env python3
"""extra Lucide icons for «واقي الشمس بالشتاء» (burgundy for cream circles, white for glass pills)"""
import io, cairosvg
from PIL import Image
O = "/home/user/ws/pkg/footage/"; D = "/home/user/ws/icons/"
def icon(name, size, col, out, stroke=1.8):
    svg = open(D + name + ".svg").read().replace("currentColor", "#%02x%02x%02x" % col).replace('stroke-width="2"', f'stroke-width="{stroke}"')
    Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size))).convert("RGBA").save(O + out + ".png")
B = (0x6C, 0x0D, 0x2B); Wt = (255, 255, 255)
for n in ("watch", "smartphone", "shield-check", "snowflake", "cloud-sun", "sun"): icon(n, 84, B, "icon_" + n.replace("-", "_"))
for n in ("repeat", "snowflake", "sun", "timer"): icon(n, 56, Wt, "icon_" + n + "_white", 2.2)
print("ok")
