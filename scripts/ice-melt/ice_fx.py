#!/usr/bin/env python3
"""ice_fx: procedural frost / ice sheet that freezes over and melts away, revealing the content under it.
Fields are cached in WORK/fields.npz. Everything is float32, 1080x1920.
render_ice(C, top, t) -> final RGB frame, also returns the passes used for the AE package."""
import os, math
import numpy as np, cv2
from scipy.spatial import cKDTree

W, H = 1080, 1920
WORK = os.environ.get("ICE_WORK", "/home/user/ice/work")
os.makedirs(WORK, exist_ok=True)

def smooth(e0, e1, x):
    x = np.clip((x - e0) / (e1 - e0), 0, 1)
    return x * x * (3 - 2 * x)
def sm1(x):
    x = min(max(x, 0.0), 1.0); return x * x * (3 - 2 * x)
def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2

def fbm(seed, base, octaves, pers=0.5, aniso=1.0):
    rng = np.random.default_rng(seed); out = np.zeros((H, W), np.float32); amp = 1.0; tot = 0; s = base
    for _ in range(octaves):
        gw, gh = max(2, int(W / (s * aniso)) + 3), max(2, int(H / s) + 3)
        g = rng.random((gh, gw)).astype(np.float32)
        up = cv2.resize(g, (int(gw * s * aniso), int(gh * s)), interpolation=cv2.INTER_CUBIC)[:H, :W]
        out += up * amp; tot += amp; amp *= pers; s /= 2
    out /= tot
    lo, hi = np.percentile(out, 1), np.percentile(out, 99)
    return np.clip((out - lo) / (hi - lo), 0, 1)

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)

def build_fields():
    p = os.path.join(WORK, "fields.npz")
    if os.path.exists(p):
        return dict(np.load(p))
    F = {}
    F["frost"] = fbm(11, 260, 6, 0.55)
    F["grain"] = fbm(12, 5, 2, 0.6)
    F["mist"] = fbm(13, 90, 4, 0.5)
    # ---- crystal facets (voronoi) + crack network
    rng = np.random.default_rng(14)
    pts = np.c_[rng.uniform(-60, W + 60, 140), rng.uniform(-60, H + 60, 140)]
    tree = cKDTree(pts)
    q = np.c_[XX.ravel(), YY.ravel()]
    d, i = tree.query(q, k=2)
    d1, d2 = d[:, 0].reshape(H, W), d[:, 1].reshape(H, W); idx = i[:, 0].reshape(H, W)
    nrm = rng.normal(0, 1, (len(pts), 2)); nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    cx, cy = pts[idx, 0], pts[idx, 1]
    F["facet"] = ((XX - cx) * nrm[idx, 0] + (YY - cy) * nrm[idx, 1]).astype(np.float32) / 120.0
    F["facet_lvl"] = rng.uniform(-1, 1, len(pts)).astype(np.float32)[idx]
    edge = (d2 - d1).astype(np.float32)
    vis = fbm(15, 300, 3) > 0.42
    F["crack"] = (np.clip(1.6 - edge, 0, 1) * vis).astype(np.float32)
    F["crack_fine"] = np.clip(1.0 - edge / 0.9, 0, 1).astype(np.float32) * (fbm(16, 120, 3) > 0.62)
    # fine scratches
    sc = np.zeros((H, W), np.uint8)
    for _ in range(260):
        x0, y0 = rng.uniform(0, W), rng.uniform(0, H); a = rng.uniform(0, math.pi); L = rng.uniform(20, 140)
        x1, y1 = x0 + math.cos(a) * L, y0 + math.sin(a) * L
        cv2.line(sc, (int(x0 * 4), int(y0 * 4)), (int(x1 * 4), int(y1 * 4)), int(rng.uniform(60, 200)), 1, cv2.LINE_AA, shift=2)
    F["scratch"] = sc.astype(np.float32) / 255
    # edge-distance (for freeze from the borders)
    bd = np.minimum(np.minimum(XX, W - 1 - XX), np.minimum(YY, H - 1 - YY)) / (W / 2)
    F["border"] = np.clip(bd, 0, 1).astype(np.float32)
    # feathery frost streaks (anisotropic ridged noise), used on the freeze front
    r = fbm(17, 18, 3, 0.55); F["feather"] = (1 - np.abs(2 * r - 1)) ** 3
    F["streak"] = fbm(18, 30, 2, 0.5, aniso=0.15)        # tall vertical water streaks
    np.savez(p, **F)
    return F

F = build_fields()

ICE_HI = np.array([252, 253, 255], np.float32)
ICE_LO = np.array([214, 228, 240], np.float32)
CRACK_C = np.array([150, 178, 204], np.float32)

def ice_color(t):
    """RGB of the frost surface (premium: cool white, faceted, grain, cracks)"""
    f = F["frost"]; fac = np.clip(0.5 + 0.22 * F["facet"] + 0.12 * F["facet_lvl"], 0, 1)
    k = np.clip(0.55 * f + 0.45 * fac, 0, 1)
    c = ICE_LO[None, None] * (1 - k[..., None]) + ICE_HI[None, None] * k[..., None]
    c += ((F["grain"] - 0.5) * 14)[..., None]
    c += (F["scratch"] * 22)[..., None]
    return c

class Ev:
    def __init__(self, kind, t0, t1, seed, origins=None, crack_at=None, crack_origin=None):
        self.kind, self.t0, self.t1 = kind, t0, t1
        self.crack_at, self.crack_origin = crack_at, crack_origin
        if kind == "melt":
            dist = np.full((H, W), 1e9, np.float32)
            for (ox, oy, w) in origins:
                dist = np.minimum(dist, np.hypot(XX - ox, YY - oy) * w)
            dist /= dist.max()
            N = 0.74 * dist + 0.20 * fbm(seed, 260, 3, 0.45) + 0.06 * fbm(seed + 1, 40, 3, 0.5)
        else:
            N = 0.70 * F["border"] + 0.24 * fbm(seed, 200, 3, 0.5) + 0.06 * F["feather"]
        N = (N - N.min()) / (N.max() - N.min())
        self.N = N.astype(np.float32)
        rng = np.random.default_rng(seed + 50)
        self.drops = []
        if kind == "melt":
            for _ in range(34):
                x, y = rng.uniform(70, W - 70), rng.uniform(380, H - 260)
                r = rng.choice([rng.uniform(6, 10), rng.uniform(11, 19)], p=[0.55, 0.45])
                appear = t0 + (t1 - t0) * float(self.N[int(y), int(x)]) * 0.98
                self.drops.append(dict(x=x, y=y, r=r, ta=appear, life=rng.uniform(1.2, 2.2),
                                       vy=rng.choice([0, 0, rng.uniform(25, 70)])))

    def prog(self, t):
        return ease_io((t - self.t0) / (self.t1 - self.t0))

def state(EVS, t):
    """ice coverage (cov), thickness (th), front band, wet band; None when no ice at all"""
    cur = None; full = None
    for e in EVS:
        if t < e.t0: break
        cur = e
    if cur is None: return "full", None
    p = cur.prog(t)
    if cur.kind == "melt":
        if t >= cur.t1: return "none", cur
        thr = -0.03 + p * 1.08
        cov = smooth(thr, thr + 0.012, cur.N)
        th = smooth(thr, thr + 0.07, cur.N)
        return "melt", (cur, thr, cov, th)
    else:
        if t >= cur.t1: return "full", cur
        thr = -0.03 + p * 1.08
        cov = 1 - smooth(thr - 0.02, thr, cur.N)
        th = 1 - smooth(thr - 0.14, thr, cur.N)
        return "freeze", (cur, thr, cov, th)

def blur_small(img, f=4, sig=6):
    h, w = img.shape[:2]
    s = cv2.resize(img, (w // f, h // f), interpolation=cv2.INTER_AREA)
    s = cv2.GaussianBlur(s, (0, 0), sig)
    return cv2.resize(s, (w, h), interpolation=cv2.INTER_LINEAR)

def grad_small(m, f=4, sig=3):
    h, w = m.shape
    s = cv2.resize(m, (w // f, h // f), interpolation=cv2.INTER_AREA)
    s = cv2.GaussianBlur(s, (0, 0), sig)
    gx = cv2.Sobel(s, cv2.CV_32F, 1, 0, ksize=3) / 8; gy = cv2.Sobel(s, cv2.CV_32F, 0, 1, ksize=3) / 8
    gx = cv2.resize(gx, (w, h)); gy = cv2.resize(gy, (w, h))
    return gx, gy

SPARK = None
def sparkles(t, amount):
    """small twinkling crystal glints on the frost surface"""
    global SPARK
    if SPARK is None:
        rng = np.random.default_rng(77)
        SPARK = [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(0, 6.28), rng.uniform(1.5, 3.5), rng.uniform(2, 5)) for _ in range(260)]
    out = np.zeros((H, W), np.float32)
    for x, y, ph, sp, sz in SPARK:
        v = max(0.0, math.sin(t * sp + ph)) ** 10 * amount
        if v < 0.05: continue
        xi, yi = int(x), int(y)
        L = int(sz * 2.5)
        cv2.line(out, (xi - L, yi), (xi + L, yi), v * 0.8, 1, cv2.LINE_AA)
        cv2.line(out, (xi, yi - L), (xi, yi + L), v * 0.8, 1, cv2.LINE_AA)
        cv2.circle(out, (xi, yi), max(1, int(sz * 0.5)), v, -1, cv2.LINE_AA)
    return cv2.GaussianBlur(out, (0, 0), 0.8)

_CR = {}
def crack_lines(origin, seed):
    """radial fracture polylines (with branches) from the impact point: list of (pts, start_dist, width)"""
    if (origin, seed) in _CR: return _CR[(origin, seed)]
    rng = np.random.default_rng(seed); out = []
    def walk(x, y, ang, L, w, d0, depth):
        pts = [(x, y)]; d = d0
        while L > 0:
            st = rng.uniform(14, 34); ang += rng.normal(0, 0.28)
            x += math.cos(ang) * st; y += math.sin(ang) * st; d += st; L -= st
            pts.append((x, y))
            if depth < 2 and rng.random() < 0.07:
                walk(x, y, ang + rng.choice([-1, 1]) * rng.uniform(0.5, 1.0), L * rng.uniform(0.3, 0.6), w * 0.6, d, depth + 1)
        out.append((np.array(pts, np.float32), d0, w))
    n = 9
    for k in range(n):
        a0 = k * 2 * math.pi / n + rng.normal(0, 0.25)
        walk(origin[0], origin[1], a0, rng.uniform(260, 620), rng.uniform(1.6, 2.6), 0, 0)
    # concentric shards ring
    for r in (40, 95):
        pts = [(origin[0] + math.cos(q) * r * rng.uniform(0.85, 1.15), origin[1] + math.sin(q) * r * rng.uniform(0.85, 1.15)) for q in np.linspace(0, 2 * math.pi, 14)]
        out.append((np.array(pts, np.float32), r, 1.2))
    _CR[(origin, seed)] = out
    return out

def crack_mask(e, t):
    if e is None or e.crack_at is None or t < e.crack_at: return None
    reach = 700 * sm1((t - e.crack_at) / 0.30) ** 0.5
    m = np.zeros((H, W), np.uint8)
    for pts, d0, w in crack_lines(tuple(e.crack_origin), int(e.t0 * 10)):
        seg = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))] + d0
        keep = pts[seg <= reach]
        if len(keep) < 2: continue
        cv2.polylines(m, [np.round(keep * 4).astype(np.int32)], False, 255, max(1, int(round(w))), cv2.LINE_AA, shift=2)
    mf = m.astype(np.float32) / 255
    return np.maximum(mf, cv2.GaussianBlur(mf, (0, 0), 2.5) * 0.5)

def render(C, top, t, EVS, glint=None, sparkle_amt=1.0, passes=False):
    """C: content RGB float (H,W,3). top: premult RGBA drawn ON the ice surface (or None)."""
    kind, st = state(EVS, t)
    out = C.copy()
    # upcoming melt -> cracks on the full ice
    nxt = next((e for e in EVS if e.kind == "melt" and e.crack_at is not None and e.crack_at <= t <= e.t1), None)
    if kind == "none":
        cov = None
    else:
        if kind == "full":
            cov = np.ones((H, W), np.float32); th = np.ones((H, W), np.float32); front = None
        else:
            e, thr, cov, th = st
            front = (e, thr)
        fa = (0.90 + 0.08 * F["frost"]) * (0.30 + 0.70 * th)
        # refraction through the ice (thin ice refracts most near the melt edge)
        gx, gy = grad_small(th)
        disp = 70.0
        mx = (XX + gx * disp).astype(np.float32); my = (YY + gy * disp).astype(np.float32)
        Cr = cv2.remap(C, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        Cb = blur_small(Cr, 4, 4 + 5 * float(th.mean()))
        thk = th[..., None]
        under = Cr * (1 - thk) + Cb * thk
        I = ice_color(t)
        if top is not None:
            a = top[..., 3:4] / 255 * smooth(0.25, 0.7, th)[..., None]
            I = I * (1 - a) + top[..., :3] / np.maximum(top[..., 3:4], 1e-3) * 255 * a * (0.92 + 0.08 * F["grain"][..., None])
        ice = under * (1 - fa[..., None]) + I * fa[..., None]
        # lighting of the ice relief: light from top-left
        lx, ly = -0.6, -0.8
        nd = gx * lx + gy * ly
        spec = np.clip(nd * 26, 0, 1) ** 1.5
        shade = np.clip(-nd * 18, 0, 1)
        ice += (spec * 120)[..., None]
        ice *= (1 - 0.18 * shade)[..., None]
        # cracks before the melt
        if nxt is not None:
            cm = crack_mask(nxt, t)
            if cm is not None:
                cm1 = np.roll(cm, 1, axis=0)
                ice = ice * (1 - 0.55 * cm[..., None]) + CRACK_C * 0.55 * cm[..., None]
                ice += (cm1 * 70 * (1 - cm))[..., None]
        if front is not None and front[0].kind == "freeze":
            e, thr = front
            band = np.exp(-((e.N - thr) / 0.025) ** 2) * (0.5 + 0.8 * F["feather"])
            ice += (band * 90)[..., None]
        if glint is not None:
            g = glint(t)
            if g is not None:
                s = (XX * 0.55 + YY * 0.85)
                b = np.exp(-((s - g) / 70) ** 2) * 0.55 + np.exp(-((s - g + 160) / 22) ** 2) * 0.35
                ice += (b * 55 * fa)[..., None]
        sp = sparkles(t, sparkle_amt) * fa
        ice += (sp * 200)[..., None]
        out = C * (1 - cov[..., None]) + ice * cov[..., None]
        # wet rim right outside the ice edge (water line) + highlight
        if kind == "melt":
            e, thr = front
            rim = np.exp(-((e.N - thr + 0.006) / 0.006) ** 2)
            out += (rim * 55)[..., None]
            wet = smooth(thr - 0.10, thr - 0.005, e.N) * (e.N < thr)
            out += (wet * (F["streak"] - 0.45) * 14)[..., None]
    # droplets on the freshly melted surface
    for e in EVS:
        if e.kind != "melt" or t < e.t0 or t > e.t1 + 2.6: continue
        draw_drops(out, C, e, t)
    return np.clip(out, 0, 255)

from scipy.ndimage import map_coordinates
def draw_drops(out, C, e, t):
    for d in e.drops:
        age = t - d["ta"]
        if age < 0 or age > d["life"]: continue
        a = sm1(age / 0.18) * (1 - sm1((age - d["life"] + 0.5) / 0.5))
        r = d["r"] * (0.4 + 0.6 * sm1(age / 0.18))
        cx = d["x"]; cy = d["y"] + d["vy"] * max(0, age - 0.3) ** 1.3
        x0, x1 = int(cx - r - 5), int(cx + r + 6); y0, y1 = int(cy - r - 5), int(cy + r + 7)
        if x0 < 0 or y0 < 0 or x1 >= W or y1 >= H: continue
        ys, xs = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        dx, dy = xs - cx, ys - cy
        dd = np.hypot(dx, dy) / r
        inside = np.clip((1 - dd) * r, 0, 1)
        sx = np.clip(cx - dx * 1.4, 0, W - 1); sy = np.clip(cy - dy * 1.4, 0, H - 1)
        lens = np.dstack([map_coordinates(C[..., c], [sy, sx], order=1) for c in range(3)])
        lens = lens * 1.18 + 14
        rim = np.clip((dd - 0.72) / 0.28, 0, 1) ** 2
        lens = lens * (1 - 0.45 * rim * (dy > -0.2 * r))[..., None]
        hl = np.exp(-(((dx + 0.32 * r) / (0.20 * r)) ** 2 + ((dy + 0.36 * r) / (0.15 * r)) ** 2)) * 235
        caus = np.exp(-(((dx - 0.05 * r) / (0.42 * r)) ** 2 + ((dy - 0.58 * r) / (0.14 * r)) ** 2)) * 70
        sh = np.exp(-((np.hypot(dx - 2, dy - 3) / r - 1.02) / 0.16) ** 2) * 0.30
        reg = out[y0:y1, x0:x1]
        reg *= (1 - sh * a * (1 - inside))[..., None]
        m = (inside * a)[..., None]
        reg[:] = reg * (1 - m) + (lens + (hl + caus)[..., None]) * m
