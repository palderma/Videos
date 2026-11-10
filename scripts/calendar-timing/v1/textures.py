"""Page / board textures for the 3D calendar (straight-alpha float RGBA -> returned premultiplied)."""
import numpy as np, cv2, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from tl import BURG, PINK, FILLED

TS = 1.6                     # texture px per world unit
PW, PH = 580, 720            # page size (world)
TW, TH = int(PW * TS), int(PH * TS)
FONT = "/home/user/Videos/brand/fonts/thmanyahsans-%s.otf"
LOGO = "/home/user/Videos/brand/logo/"
RING_X = None                # filled below
NRING = 13
RING_X = [(-PW / 2 + 38) + i * (PW - 76) / (NRING - 1) for i in range(NRING)]
rng = np.random.default_rng(7)

def _grain(h, w, amt):
    g = rng.standard_normal((h // 2 + 1, w // 2 + 1)).astype(np.float32)
    g = cv2.resize(g, (w, h), interpolation=cv2.INTER_LINEAR)[:h, :w]
    return g * amt

def _paper(col=(255, 253, 251)):
    im = np.zeros((TH, TW, 3), np.float32); im[:] = col
    # very soft fall-off + fibre grain
    yy, xx = np.mgrid[0:TH, 0:TW].astype(np.float32)
    r = np.hypot((xx - TW / 2) / TW, (yy - TH * 0.45) / TH)
    im *= (1 - 0.035 * r ** 2)[..., None]
    im += _grain(TH, TW, 1.6)[..., None]
    return im

def _holes(alpha, rgb, top_shadow=True):
    """punched holes for the wire-o rings + a soft contact shadow under the binding"""
    for x in RING_X:
        for dx in (-4.2, 4.2):
            cx = int((x + dx + PW / 2) * TS); cy = int(11 * TS)
            cv2.ellipse(alpha, (cx, cy), (int(2.4 * TS), int(3.6 * TS)), 0, 0, 360, 0.0, -1, cv2.LINE_AA)
    if top_shadow:
        yy = np.arange(TH, dtype=np.float32)[:, None]
        sh = np.exp(-yy / (14 * TS)) * 0.10
        rgb *= (1 - sh)[..., None]

def _text_mask(txt, size, weight="Black"):
    f = ImageFont.truetype(FONT % weight, size, layout_engine=ImageFont.Layout.RAQM)
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    bb = d.textbbox((0, 0), txt, font=f, anchor="ls")
    w, h = bb[2] - bb[0] + 40, bb[3] - bb[1] + 40
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((20 - bb[0], 20 - bb[1]), txt, font=f, fill=255, anchor="ls")
    return np.array(m, np.float32) / 255

def _paste_mask(rgb, mask, col, cx, cy, op=1.0):
    h, w = mask.shape
    x0, y0 = int(cx - w / 2), int(cy - h / 2)
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(rgb.shape[1], x0 + w), min(rgb.shape[0], y0 + h)
    m = mask[ya - y0:yb - y0, xa - x0:xb - x0, None] * op
    rgb[ya:yb, xa:xb] = rgb[ya:yb, xa:xb] * (1 - m) + np.array(col, np.float32) * m

def _logo(name, color, width):
    im = Image.open(LOGO + "%s/png/%s.png" % (name, color)).convert("RGBA")
    h = int(im.height * width / im.width)
    im = im.resize((int(width), h), Image.LANCZOS)
    a = np.array(im, np.float32)
    return a[..., 3] / 255

def _star(size):
    """four-point sparkle like the star in the Palderma rosette"""
    s = size * 4
    m = Image.new("L", (s, s), 0); d = ImageDraw.Draw(m)
    c = s / 2; pts = []
    for i in range(16):
        ang = np.pi / 2 * (i / 4)
        r = c * 0.98 if i % 4 == 0 else c * (0.16 if i % 2 == 0 else 0.10)
        # concave star: tips at 0/90/180/270
    pts = []
    N = 400
    for i in range(N):
        a = 2 * np.pi * i / N
        # astroid-like sparkle: |x|^p + |y|^p = r^p with p < 1
        p = 0.55
        ca, sa = np.cos(a), np.sin(a)
        r = (abs(ca) ** p + abs(sa) ** p) ** (-1 / p)
        pts.append((c + r * ca * c * 0.98, c + r * sa * c * 0.98))
    d.polygon(pts, fill=255)
    m = m.resize((size, size), Image.LANCZOS)
    return np.array(m, np.float32) / 255

def _finish(rgb, alpha):
    a = alpha.copy()
    # rounded corners on the free edge
    rr = int(9 * TS)
    for (cx, cy) in ((rr, TH - rr), (TW - rr, TH - rr)):
        yy, xx = np.mgrid[0:TH, 0:TW]
        pass
    yy, xx = np.mgrid[0:TH, 0:TW].astype(np.float32)
    for cx in (rr, TW - rr):
        cy = TH - rr
        sel = ((xx < rr) if cx == rr else (xx > TW - rr)) & (yy > TH - rr)
        d = np.hypot(xx - cx, yy - cy)
        a = np.where(sel, a * np.clip(rr - d + 0.5, 0, 1), a)
    # 2px transparent border for clean AA of the outer edge
    out = np.zeros((TH + 4, TW + 4, 4), np.float32)
    out[2:-2, 2:-2, :3] = np.clip(rgb, 0, 255) * a[..., None]
    out[2:-2, 2:-2, 3] = a * 255
    return out

_cache = {}
def page_tex(name, fill=1.0):
    """front texture of a page; fill = 0..1 animation of the week bars (numbered pages)"""
    q = round(fill * 40) / 40
    k = (name, q)
    if k in _cache: return _cache[k]
    alpha = np.ones((TH, TW), np.float32)
    if name == "cover":
        yy = np.arange(TH, dtype=np.float32)[:, None] / TH
        top, bot = np.array((247, 182, 202), np.float32), np.array((238, 154, 181), np.float32)
        rgb = np.zeros((TH, TW, 3), np.float32) + (top + (bot - top) * yy)[:, None, :]
        rgb += _grain(TH, TW, 1.2)[..., None]
        wm = _logo("english", "burgundy", 400 * TS)
        _paste_mask(rgb, wm, BURG, TW / 2, TH * 0.52)
        _holes(alpha, rgb)
    elif name == "event":
        yy = np.arange(TH, dtype=np.float32)[:, None] / TH
        rgb = _paper()
        st = _star(int(250 * TS))
        g = cv2.GaussianBlur(np.pad(st, 80), (0, 0), 34)
        _paste_mask(rgb, np.clip(g * 1.4, 0, 1), (250, 214, 226), TW / 2, TH * 0.49, 0.8)
        _paste_mask(rgb, st, PINK, TW / 2, TH * 0.49)
        _holes(alpha, rgb)
    else:
        rgb = _paper()
        # brand wordmark small at the head of the page
        wm = _logo("english", "burgundy", 118 * TS)
        _paste_mask(rgb, wm, BURG, TW / 2, 70 * TS, 0.9)
        # the big numeral, letter-pressed (soft deboss)
        num = _text_mask(name, int(560 * TS), "Black")
        sh = cv2.GaussianBlur(num, (0, 0), 2.2 * TS)
        cy = TH * 0.50
        _paste_mask(rgb, sh, (225, 205, 210), TW / 2, cy + 2.4 * TS, 0.55)
        _paste_mask(rgb, num, BURG, TW / 2, cy)
        # highlight on the upper inner edge of the ink
        hi = np.clip(num - np.roll(num, int(1.2 * TS), axis=0), 0, 1)
        _paste_mask(rgb, hi, (150, 40, 75), TW / 2, cy, 0.45)
        # week bars: 4 slots, filled = weeks left, RTL fill
        n = FILLED[name]
        bw, bh, gap = 86 * TS, 13 * TS, 18 * TS
        total = 4 * bw + 3 * gap
        y0 = TH * 0.855
        for i in range(4):                       # i = 0 is the RIGHT-most bar
            x1 = TW / 2 + total / 2 - i * (bw + gap); x0 = x1 - bw
            base = np.zeros((TH, TW), np.float32)
            cv2.rectangle(base, (int(x0), int(y0)), (int(x1), int(y0 + bh)), 1.0, -1)
            base = _round_bar(x0, y0, bw, bh)
            _paste_full(rgb, base, (246, 232, 237))
            if i < n:
                f = np.clip(fill * n - i, 0, 1)
                if f > 0:
                    fx0 = x1 - bw * f
                    m = _round_bar(fx0, y0, x1 - fx0, bh)
                    _paste_full(rgb, m, PINK)
        _holes(alpha, rgb)
    out = _finish(rgb, alpha)
    _cache[k] = out
    return out

def _round_bar(x0, y0, w, h):
    m = np.zeros((TH, TW), np.uint8)
    r = h / 2
    s = 4
    if w < 1: return m.astype(np.float32)
    cv2.rectangle(m, (int((x0 + r) * 16), int(y0 * 16)), (int((x0 + max(w, 2 * r) - r) * 16), int((y0 + h) * 16)), 255, -1, cv2.LINE_AA, 4)
    cv2.circle(m, (int((x0 + r) * 16), int((y0 + r) * 16)), int(r * 16), 255, -1, cv2.LINE_AA, 4)
    cv2.circle(m, (int((x0 + max(w, 2 * r) - r) * 16), int((y0 + r) * 16)), int(r * 16), 255, -1, cv2.LINE_AA, 4)
    return m.astype(np.float32) / 255

def _paste_full(rgb, m, col):
    rgb[:] = rgb * (1 - m[..., None]) + np.array(col, np.float32) * m[..., None]

_bcache = {}
def back_tex(name):
    if name in _bcache: return _bcache[name]
    alpha = np.ones((TH, TW), np.float32)
    if name == "cover":
        rgb = np.zeros((TH, TW, 3), np.float32); rgb[:] = (236, 160, 184); rgb += _grain(TH, TW, 1.2)[..., None]
    else:
        rgb = _paper((246, 242, 240))
        f = page_tex(name, 1.0)
        ink = 1 - (f[2:-2, 2:-2, :3].mean(2) / 255)         # show-through of the print (mirrors by itself)
        rgb -= ink[..., None] * 10
    _holes(alpha, rgb, top_shadow=False)
    out = _finish(rgb, alpha); _bcache[name] = out
    return out

# board (backing) -----------------------------------------------------------
BW, BH = 640, 820
BTW, BTH = int(BW * 1.2), int(BH * 1.2)
def board_tex():
    k = "board"
    if k in _bcache: return _bcache[k]
    yy, xx = np.mgrid[0:BTH, 0:BTW].astype(np.float32)
    top, bot = np.array((242, 222, 228), np.float32), np.array((222, 190, 201), np.float32)
    rgb = top + (bot - top) * (yy / BTH)[..., None]
    rgb += _grain(BTH, BTW, 2.0)[..., None]
    # bevel: light along top/left edge, dark along bottom/right
    e = 6 * 1.2
    dl = np.minimum(xx, yy); dr = np.minimum(BTW - xx, BTH - yy)
    rgb += (np.clip(1 - dl / e, 0, 1) * 38)[..., None] * np.array((1.0, 0.75, 0.82))
    rgb -= (np.clip(1 - dr / e, 0, 1) * 30)[..., None]
    a = np.ones((BTH, BTW), np.float32)
    rr = 14 * 1.2
    for cx, cy in ((rr, rr), (BTW - rr, rr), (rr, BTH - rr), (BTW - rr, BTH - rr)):
        sel = (np.abs(xx - cx) <= rr) & (np.abs(yy - cy) <= rr) & ((xx - cx) * (BTW / 2 - cx) < 0) & ((yy - cy) * (BTH / 2 - cy) < 0)
        d = np.hypot(xx - cx, yy - cy)
        a = np.where(sel, a * np.clip(rr - d + 0.5, 0, 1), a)
    out = np.zeros((BTH + 4, BTW + 4, 4), np.float32)
    out[2:-2, 2:-2, :3] = np.clip(rgb, 0, 255) * a[..., None]; out[2:-2, 2:-2, 3] = a * 255
    _bcache[k] = out
    return out

def edge_tex(n=9, h=64, col=(250, 246, 244)):
    """paper-stack edge: fine horizontal sheets"""
    k = ("edge", n)
    if k in _bcache: return _bcache[k]
    im = np.zeros((h, 8, 4), np.float32)
    for y in range(h):
        s = (y * n / h) % 1
        v = 1 - 0.22 * (abs(s - 0.5) > 0.38)
        im[y, :, :3] = np.array(col) * v
    im[..., 3] = 255
    _bcache[k] = im
    return im

if __name__ == "__main__":
    import sys
    for nm in ("cover", "4", "2", "event"):
        t = page_tex(nm, 0.6)
        a = t[..., 3:4] / 255
        rgb = t[..., :3] + (1 - a) * 80
        Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).resize((TW // 2, TH // 2)).save("/home/user/cal/tex_%s.png" % nm)
