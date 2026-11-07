#!/usr/bin/env python3
"""Static PNG assets for «الشد المائي خرافة» (pkg/footage): pink->wine motion background, wine flower,
bottom caption shade, Lucide icons, logo."""
import os, io, numpy as np, cv2, cairosvg
from PIL import Image
O = "/home/user/klf/pkg2/footage"; os.makedirs(O, exist_ok=True)
W, H = 1080, 1920
YS, XS = np.mgrid[0:H, 0:W].astype(np.float32) + 0.5

# radial pink -> wine (same stops as «تجمع سوائل»)
cx, cy = W / 2, H * 0.47
r = np.hypot((XS - cx) / (W * 0.85), (YS - cy) / (H * 0.62))
stops = [(0.0, (0xD5, 0x89, 0xA8)), (0.45, (0xBB, 0x62, 0x88)), (0.85, (0x8A, 0x25, 0x52)), (1.15, (0x6D, 0x0B, 0x34)), (1.6, (0x63, 0x00, 0x2A))]
bg = np.zeros((H, W, 3), np.float32) + np.array(stops[-1][1], np.float32)
for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
    m = ((r >= p0) & (r < p1))[..., None]; k = ((r - p0) / (p1 - p0))[..., None]
    bg = np.where(m, np.array(c0, np.float32) * (1 - k) + np.array(c1, np.float32) * k, bg)
bg += np.random.default_rng(1).normal(0, 1.2, bg.shape)          # tiny grain: no banding
Image.fromarray(bg.clip(0, 255).astype(np.uint8)).save(f"{O}/bg_pink_wine.png")

if False:
  pass
# user's 6-petal flower, coloured wine, transparent
src = np.array(Image.open("/mnt/project-files/style-guide/assets/وردة-6-بتلات.png").convert("RGBA"), np.float32) / 255
m = src[..., 3] * np.clip((0.85 - src[..., :3].mean(-1)) / 0.5, 0, 1)
ys, xs = np.nonzero(m > 0.5); fcy, fcx = (ys.min() + ys.max()) / 2, (xs.min() + xs.max()) / 2
half = max(ys.max() - ys.min(), xs.max() - xs.min()) / 2 * 1.04; S = 1200
M = np.float32([[S / (2 * half), 0, S / 2 - fcx * S / (2 * half)], [0, S / (2 * half), S / 2 - fcy * S / (2 * half)]])
a = cv2.GaussianBlur(cv2.warpAffine(m, M, (S, S), flags=cv2.INTER_AREA), (0, 0), 1.2)
fl = np.zeros((S, S, 4), np.uint8); fl[..., :3] = (0x6C, 0x0D, 0x2B); fl[..., 3] = (a * 255).clip(0, 255)
Image.fromarray(fl).save(f"{O}/flower_wine.png")

# dark caption shade (bottom)
g = np.clip((YS[:, :1] - 1080) / 700, 0, 1) ** 1.3 * 0.78
sh = np.zeros((H, W, 4), np.uint8); sh[..., :3] = (22, 2, 9); sh[..., 3] = np.repeat(g * 255, W, 1).astype(np.uint8)
Image.fromarray(sh).save(f"{O}/shade_bottom.png")

g = (1 - np.clip((YS[:, :1] - 120) / 380, 0, 1)) ** 1.6 * 0.55
sh = np.zeros((H, W, 4), np.uint8); sh[..., :3] = (22, 2, 9); sh[..., 3] = np.repeat(g * 255, W, 1).astype(np.uint8)
Image.fromarray(sh).save(f"{O}/shade_top.png")

# one soft light (replaces the flowers, v2)
L = 1100; yy, xx = np.mgrid[0:L, 0:L].astype(np.float32) + 0.5
d = np.hypot(xx - L / 2, yy - L / 2) / (L / 2)
al = np.clip(1 - d, 0, 1) ** 2.2 * 0.55
lt = np.zeros((L, L, 4), np.uint8); lt[..., :3] = (255, 226, 236); lt[..., 3] = (al * 255).astype(np.uint8)
Image.fromarray(lt).save(f"{O}/soft_light.png")

# icons
ICON_DIRS = ["/mnt/project-files/edits/scl_work/icons", "/mnt/project-files/edits/hl2_work/icons"]
def icon(name, size, col, out, stroke=1.8):
    for d in ICON_DIRS:
        p = os.path.join(d, name + ".svg")
        if os.path.exists(p): break
    svg = open(p).read().replace("currentColor", "#%02x%02x%02x" % col).replace('stroke-width="2"', f'stroke-width="{stroke}"')
    Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size))).convert("RGBA").save(f"{O}/{out}.png")
BURG = (0x6C, 0x0D, 0x2B)
for nm in ("scroll-text", "droplets", "timer", "droplet", "cloud-sun", "search", "calendar-heart", "calendar"):
    icon(nm, 96, BURG, "icon_" + nm.replace("-", "_"), 1.8)
icon("x", 40, (255, 255, 255), "icon_x_white", 3.0)
icon("calendar", 52, (255, 255, 255), "icon_calendar_white", 2.0)
icon("search", 64, (255, 255, 255), "icon_search_white", 2.0)
icon("calendar-heart", 60, (255, 255, 255), "icon_calendar_heart_white", 2.0)

lg = Image.open("/home/user/Videos/brand/logo/arabic-english/png/white.png").convert("RGBA")
bb = lg.getbbox(); lg = lg.crop(bb); lg.thumbnail((620, 620)); lg.save(f"{O}/logo_white.png")
ic = Image.open("/home/user/Videos/brand/logo/icon/png/burgundy.png").convert("RGBA"); ic = ic.crop(ic.getbbox()); ic.thumbnail((150, 150)); ic.save(f"{O}/logo_icon_burgundy.png")
Image.open("/mnt/project-files/style-guide/assets/templates/frame-9x16.png").save(f"{O}/frame_template_9x16.png")
print("ok", lg.size)
