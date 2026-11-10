#!/usr/bin/env python3
"""Static assets for «بوتوكس الرجال» (pkg/footage): pink->wine motion background, soft light, bottom caption shade,
Lucide line icons, brand frame, and the user's approved WhatsApp pill + pink outro (copied unchanged)."""
import os, io, shutil, numpy as np, cairosvg
from PIL import Image
O = "/home/user/bm/pkg/footage"; os.makedirs(O, exist_ok=True)
W, H = 1080, 1920
YS, XS = np.mgrid[0:H, 0:W].astype(np.float32) + 0.5
cx, cy = W / 2, H * 0.47
r = np.hypot((XS - cx) / (W * 0.85), (YS - cy) / (H * 0.62))
stops = [(0.0, (0xD5, 0x89, 0xA8)), (0.45, (0xBB, 0x62, 0x88)), (0.85, (0x8A, 0x25, 0x52)), (1.15, (0x6D, 0x0B, 0x34)), (1.6, (0x63, 0x00, 0x2A))]
bg = np.zeros((H, W, 3), np.float32) + np.array(stops[-1][1], np.float32)
for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
    m = ((r >= p0) & (r < p1))[..., None]; k = ((r - p0) / (p1 - p0))[..., None]
    bg = np.where(m, np.array(c0, np.float32) * (1 - k) + np.array(c1, np.float32) * k, bg)
bg += np.random.default_rng(1).normal(0, 1.2, bg.shape)
Image.fromarray(bg.clip(0, 255).astype(np.uint8)).save(f"{O}/bg_pink_wine.png")
g = np.clip((YS[:, :1] - 1080) / 700, 0, 1) ** 1.3 * 0.78
sh = np.zeros((H, W, 4), np.uint8); sh[..., :3] = (22, 2, 9); sh[..., 3] = np.repeat(g * 255, W, 1).astype(np.uint8)
Image.fromarray(sh).save(f"{O}/shade_bottom.png")
L = 1100; yy, xx = np.mgrid[0:L, 0:L].astype(np.float32) + 0.5
d = np.hypot(xx - L / 2, yy - L / 2) / (L / 2)
al = np.clip(1 - d, 0, 1) ** 2.2 * 0.55
lt = np.zeros((L, L, 4), np.uint8); lt[..., :3] = (255, 226, 236); lt[..., 3] = (al * 255).astype(np.uint8)
Image.fromarray(lt).save(f"{O}/soft_light.png")
ICON_DIRS = ["/mnt/project-files/edits/scl_work/icons", "/mnt/project-files/edits/hl2_work/icons"]
def icon(name, size, col, out, stroke=1.8):
    p = next(os.path.join(d, name + ".svg") for d in ICON_DIRS if os.path.exists(os.path.join(d, name + ".svg")))
    svg = open(p).read().replace("currentColor", "#%02x%02x%02x" % col).replace('stroke-width="2"', f'stroke-width="{stroke}"')
    Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size))).convert("RGBA").save(f"{O}/{out}.png")
B = (0x6C, 0x0D, 0x2B); Wt = (255, 255, 255)
for n in ("syringe", "eye", "scan-face", "timer", "sparkles", "user-round", "users-round"): icon(n, 88, B, "icon_" + n.replace("-", "_"), 1.8)
for n in ("timer", "syringe", "scan-face", "sparkles", "check"): icon(n, 58, Wt, "icon_" + n.replace("-", "_") + "_white", 2.2)
Image.open("/mnt/project-files/style-guide/assets/templates/frame-9x16.png").save(f"{O}/frame_template_9x16.png")
for src, dst in [("/mnt/project-files/after-effects/assets/whatsapp-outro-alpha.mov", "whatsapp_pill.mov"),
                 ("/mnt/project-files/style-guide/assets/خاتمة-عمودي-9x16.mp4", "palderma_pink_outro.mp4")]:
    shutil.copy(src, f"{O}/{dst}")
print("ok")
