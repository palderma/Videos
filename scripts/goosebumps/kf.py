#!/usr/bin/env python3
"""kf: a tiny After-Effects-like layer/keyframe scene graph.
The SAME scene description is (a) rendered here with numpy/OpenCV to the final MP4 and
(b) exported as an After Effects ExtendScript (.jsx) that rebuilds every layer with native keyframes
(text layers, shape layers, footage, precomps, time-remap, Gaussian Blur / Drop Shadow effects).

Keyframe easing = AE temporal ease with speed 0: a segment between key i (out influence o) and key i+1
(in influence n) follows the bezier (0,0)-(o,0)-(1-n,1)-(1,1), exactly what AE draws for those settings.
"""
import math, os, json
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = "/home/user/Videos/brand/fonts"
FONT_PS = {"Black": "thmanyahsans-Black", "Bold": "thmanyahsans-Bold", "Medium": "thmanyahsans-Medium",
           "Regular": "thmanyahsans-Regular", "Light": "thmanyahsans-Light"}

# ------------------------------------------------------------------ keyframes
class K:
    """one keyframe: t, value, in/out influence (%) ; lin=True -> linear; hold=True -> hold"""
    __slots__ = ("t", "v", "i", "o", "lin", "hold")
    def __init__(self, t, v, i=75, o=75, lin=False, hold=False):
        self.t, self.v, self.i, self.o, self.lin, self.hold = float(t), v, i, o, lin, hold

def keys(*seq, **kw):
    """keys((t, v), (t, v, in, out), ...) ; kw ease='io'|'out'|'in'|'lin'"""
    ease = kw.get("ease", "io")
    pre = {"smooth": (85, 35), "io": (75, 75), "out": (12, 88), "in": (88, 12), "soft": (60, 60), "lin": (33, 33)}[ease]
    out = []
    for s in seq:
        if isinstance(s, K): out.append(s); continue
        t, v = s[0], s[1]
        i, o = (s[2], s[3]) if len(s) >= 4 else pre
        # for 'out' ease the incoming influence belongs to the 2nd key and outgoing to the 1st key
        if ease == "out": i, o = (88, 12)
        if ease == "in": i, o = (12, 88)
        if ease == "smooth": i, o = (85, 35)
        out.append(K(t, v, i, o, lin=(ease == "lin")))
    return out

def _bez(x, o, n):
    """y for x on cubic bezier (0,0),(o,0),(1-n,1),(1,1)"""
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    x1, x2 = o, 1 - n
    lo, hi = 0.0, 1.0
    for _ in range(40):
        u = (lo + hi) / 2
        bx = 3 * (1 - u) ** 2 * u * x1 + 3 * (1 - u) * u * u * x2 + u ** 3
        if bx < x: lo = u
        else: hi = u
    u = (lo + hi) / 2
    return 3 * (1 - u) * u * u + u ** 3

def val(p, t):
    if not isinstance(p, list) or not p or not isinstance(p[0], K): return p
    if t <= p[0].t: return p[0].v
    if t >= p[-1].t: return p[-1].v
    for a, b in zip(p, p[1:]):
        if a.t <= t < b.t:
            if a.hold: return a.v
            x = (t - a.t) / (b.t - a.t)
            y = x if (a.lin and b.lin) else _bez(x, a.o / 100, b.i / 100)
            if isinstance(a.v, (list, tuple)):
                return [av + (bv - av) * y for av, bv in zip(a.v, b.v)]
            return a.v + (b.v - a.v) * y
    return p[-1].v

def animated(p): return isinstance(p, list) and p and isinstance(p[0], K)

# ------------------------------------------------------------------ layers
class Layer:
    def __init__(self, name, kind, inp=0.0, outp=None, **kw):
        self.name, self.kind, self.inp, self.outp = name, kind, inp, outp
        self.anchor = kw.pop("anchor", None)       # None -> kind default (centre / ink centre)
        self.pos = kw.pop("pos", [540, 960]); self.scale = kw.pop("scale", 100.0)
        self.rot = kw.pop("rot", 0.0); self.op = kw.pop("op", 100.0)
        self.blur = kw.pop("blur", 0.0)             # AE Gaussian Blur 'blurriness'
        self.shadow = kw.pop("shadow", None)        # dict(color, op(0-255), dist, soft, dir)
        self.parent = kw.pop("parent", None)
        self.guide = kw.pop("guide", False)
        self.enabled = kw.pop("enabled", True)
        self.comment = kw.pop("comment", "")
        self.kw = kw

def text(name, txt, size, weight="Bold", color=(255, 255, 255), **kw):
    return Layer(name, "text", txt=txt, size=size, weight=weight, color=color, **kw)
def rect(name, w, h, radius, fill=None, fill_op=100, stroke=None, stroke_w=0, stroke_op=100, **kw):
    """size may be animated: w/h given as keys on 'size' -> pass size=keys(...)"""
    size = kw.pop("size", [w, h])
    return Layer(name, "rect", size=size, radius=radius, fill=fill, fill_op=fill_op, stroke=stroke, stroke_w=stroke_w, stroke_op=stroke_op, **kw)
def ellipse(name, d, fill=None, fill_op=100, stroke=None, stroke_w=0, stroke_op=100, **kw):
    size = kw.pop("size", [d, d])
    return Layer(name, "ellipse", size=size, fill=fill, fill_op=fill_op, stroke=stroke, stroke_w=stroke_w, stroke_op=stroke_op, **kw)
def image(name, path, **kw): return Layer(name, "image", path=path, **kw)
def footage(name, path, start=0.0, remap=None, **kw):
    """start = comp time at which source time 0 plays; remap = keys of source time (comp-time keyed)"""
    return Layer(name, "footage", path=path, start=start, remap=remap, **kw)
def precomp(name, comp, start=0.0, **kw): return Layer(name, "precomp", comp=comp, start=start, **kw)
def audio(name, path, start=0.0, **kw): return Layer(name, "audio", path=path, start=start, remap=None, **kw)
def solid(name, color, w, h, **kw): return Layer(name, "solid", color=color, w=w, h=h, **kw)

class Comp:
    def __init__(self, name, w, h, dur, fps=30, bg=(0, 0, 0)):
        self.name, self.w, self.h, self.dur, self.fps, self.bg = name, w, h, dur, fps, bg
        self.layers = []           # bottom -> top
        self.markers = []          # (t, comment)
    def add(self, L): self.layers.append(L); return L

# ------------------------------------------------------------------ text raster
_fonts = {}
def font(weight, size):
    k = (weight, int(size))
    if k not in _fonts:
        _fonts[k] = ImageFont.truetype(os.path.join(FONT_DIR, FONT_PS[weight] + ".otf"), int(size), layout_engine=ImageFont.Layout.RAQM)
    return _fonts[k]

_tc = {}
def text_raster(txt, size, weight, color):
    """premultiplied RGBA float, plus origin (ox, oy) = ink-centre-x / baseline inside the raster"""
    k = (txt, int(round(size)), weight, tuple(color))
    if k in _tc: return _tc[k]
    f = font(weight, round(size)); pad = int(size * 0.5) + 10
    dr = "ltr" if all(ord(c) < 128 for c in txt) else "rtl"
    d = ImageDraw.Draw(Image.new("L", (1, 1)))
    tw = int(d.textlength(txt, font=f, direction=dr, language="ar"))
    asc, desc = f.getmetrics()
    w, h = tw + pad * 2, asc + desc + pad * 2
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).text((pad, pad + asc), txt, font=f, fill=255, direction=dr, language="ar", anchor="ls")
    a = np.array(m, np.float32) / 255
    xs = np.nonzero(a.max(0) > 0.02)[0]
    cx = (xs.min() + xs.max() + 1) / 2 if len(xs) else w / 2
    img = np.zeros((h, w, 4), np.float32)
    img[..., :3] = np.array(color, np.float32)[None, None] * a[..., None]; img[..., 3] = a * 255
    res = (img, cx, pad + asc)
    _tc[k] = res
    return res

def text_width(txt, size, weight):
    img, cx, by = text_raster(txt, size, weight, (255, 255, 255))
    xs = np.nonzero(img[..., 3].max(0) > 5)[0]
    return float(xs.max() - xs.min() + 1) if len(xs) else 0.0

# ------------------------------------------------------------------ shape raster
def shape_raster(L, t, ss=1.0):
    w, h = val(L.kw["size"], t)
    w, h = max(w, 0.5), max(h, 0.5)
    if L.kind == "rect": r = min(val(L.kw["radius"], t), w / 2, h / 2)
    else: r = None
    sw = val(L.kw.get("stroke_w", 0), t) if L.kw.get("stroke") else 0
    pad = int(math.ceil(sw)) + 3
    W, H = int(math.ceil(w + 2 * pad)), int(math.ceil(h + 2 * pad))
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32) + 0.5
    cx, cy = W / 2, H / 2
    if L.kind == "rect":
        qx = np.abs(xs - cx) - (w / 2 - r); qy = np.abs(ys - cy) - (h / 2 - r)
        d = np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r
    else:
        # ellipse sdf approx (scaled circle)
        k = np.hypot((xs - cx) / (w / 2), (ys - cy) / (h / 2))
        d = (k - 1) * min(w, h) / 2
    img = np.zeros((H, W, 4), np.float32)
    if L.kw.get("fill") is not None:
        a = np.clip(0.5 - d, 0, 1) * val(L.kw.get("fill_op", 100), t) / 100
        img[..., :3] = np.array(L.kw["fill"], np.float32) * a[..., None]; img[..., 3] = a * 255
    if sw > 0:
        # AE stroke is centred on the path
        a = np.clip(sw / 2 + 0.5 - np.abs(d), 0, 1) * val(L.kw.get("stroke_op", 100), t) / 100
        col = np.array(L.kw["stroke"], np.float32)
        img[..., :3] = img[..., :3] * (1 - a[..., None]) + col * a[..., None]
        img[..., 3] = img[..., 3] * (1 - a) + 255 * a
    return img, cx, cy

# ------------------------------------------------------------------ sources
_img = {}
def load_image(path):
    if path not in _img:
        im = np.array(Image.open(path).convert("RGBA"), np.float32)
        im[..., :3] *= im[..., 3:4] / 255
        _img[path] = im
    return _img[path]

class VideoSrc:
    """sequential-friendly frame reader; RGBA premultiplied float; alpha movs read as png sequences dirs"""
    def __init__(self, path):
        self.path = path; self.cap = None; self.idx = -1; self.frame = None
        self.seq = os.path.isdir(path)
        if self.seq:
            self.files = sorted(f for f in os.listdir(path) if f.endswith(".png")); self.n = len(self.files)
        else:
            self.cap = cv2.VideoCapture(path); self.n = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
    def get(self, i):
        i = int(max(0, min(self.n - 1, i)))
        if self.seq:
            if i != self.idx:
                self.frame = load_image(os.path.join(self.path, self.files[i])).copy() if False else self._png(i); self.idx = i
            return self.frame
        if i != self.idx:
            if i != self.idx + 1:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, i)
            ok, f = self.cap.read()
            if not ok: return self.frame
            f = cv2.cvtColor(f, cv2.COLOR_BGR2RGB).astype(np.float32)
            self.frame = np.dstack([f, np.full(f.shape[:2], 255, np.float32)]); self.idx = i
        return self.frame
    def _png(self, i):
        im = np.array(Image.open(os.path.join(self.path, self.files[i])).convert("RGBA"), np.float32)
        im[..., :3] *= im[..., 3:4] / 255
        return im
_vid = {}
def video(path, fps_dir=None):
    if path not in _vid: _vid[path] = VideoSrc(path)
    return _vid[path]

# ------------------------------------------------------------------ compositing
def blur_sigma(b): return b / 2.6           # AE blurriness -> gaussian sigma (approx.)

def composite(dst, src, M, op):
    """dst HxWx3 float (straight), src premultiplied RGBA float, M 2x3 affine src->dst"""
    H, W = dst.shape[:2]; h, w = src.shape[:2]
    corners = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]], np.float32) @ M.T
    x0, y0 = max(0, int(math.floor(corners[:, 0].min())) - 1), max(0, int(math.floor(corners[:, 1].min())) - 1)
    x1, y1 = min(W, int(math.ceil(corners[:, 0].max())) + 1), min(H, int(math.ceil(corners[:, 1].max())) + 1)
    if x0 >= x1 or y0 >= y1 or op <= 0.001: return
    M2 = M.copy(); M2[0, 2] -= x0; M2[1, 2] -= y0
    s = cv2.warpAffine(src, M2, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0))
    a = s[..., 3:4] / 255 * op
    sub = dst[y0:y1, x0:x1]
    sub *= (1 - a); sub += s[..., :3] * op

def rgba_over(dst, src, M, op):
    """dst premultiplied RGBA float (for precomps)"""
    H, W = dst.shape[:2]; h, w = src.shape[:2]
    corners = np.array([[0, 0, 1], [w, 0, 1], [0, h, 1], [w, h, 1]], np.float32) @ M.T
    x0, y0 = max(0, int(math.floor(corners[:, 0].min())) - 1), max(0, int(math.floor(corners[:, 1].min())) - 1)
    x1, y1 = min(W, int(math.ceil(corners[:, 0].max())) + 1), min(H, int(math.ceil(corners[:, 1].max())) + 1)
    if x0 >= x1 or y0 >= y1 or op <= 0.001: return
    M2 = M.copy(); M2[0, 2] -= x0; M2[1, 2] -= y0
    s = cv2.warpAffine(src, M2, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=(0, 0, 0, 0)) * op
    a = s[..., 3:4] / 255
    sub = dst[y0:y1, x0:x1]
    sub *= (1 - a); sub += s

def add_shadow(img, sh, scale):
    """drop shadow behind a premultiplied RGBA layer image (in layer space), returns bigger image + offset"""
    soft = blur_sigma(sh.get("soft", 20)) / max(scale, 0.05)
    dist = sh.get("dist", 6) / max(scale, 0.05)
    ang = math.radians(sh.get("dir", 180) - 90)
    dx, dy = math.cos(ang) * dist, math.sin(ang) * dist
    pad = int(soft * 3 + abs(dist)) + 2
    h, w = img.shape[:2]
    big = np.zeros((h + 2 * pad, w + 2 * pad, 4), np.float32)
    a = np.zeros(big.shape[:2], np.float32); a[pad:pad + h, pad:pad + w] = img[..., 3]
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    a = cv2.warpAffine(a, M, (a.shape[1], a.shape[0]))
    if soft > 0.3: a = cv2.GaussianBlur(a, (0, 0), soft)
    a *= sh.get("op", 128) / 255
    big[..., :3] = np.array(sh.get("color", (40, 3, 15)), np.float32) * (a[..., None] / 255); big[..., 3] = a
    ia = img[..., 3:4] / 255
    sub = big[pad:pad + h, pad:pad + w]
    sub[:] = sub * (1 - ia) + img
    return big, pad

def layer_matrix(L, t, ax, ay):
    p = val(L.pos, t); s = val(L.scale, t); r = val(L.rot, t)
    sx, sy = (s, s) if not isinstance(s, (list, tuple)) else (s[0], s[1])
    sx /= 100; sy /= 100
    c, n = math.cos(math.radians(r)), math.sin(math.radians(r))
    A = np.array([[c * sx, -n * sy], [n * sx, c * sy]], np.float32)
    T = np.array(p[:2], np.float32) - A @ np.array([ax, ay], np.float32)
    M = np.hstack([A, T[:, None]]).astype(np.float32)
    if L.parent is not None:
        P = parent_matrix(L.parent, t)
        M = np.vstack([P, [0, 0, 1]]) @ np.vstack([M, [0, 0, 1]]); M = M[:2].astype(np.float32)
    return M

def parent_matrix(L, t):
    an = val(L.anchor, t) if L.anchor is not None else default_anchor_static(L)
    return layer_matrix(L, t, an[0], an[1])

def default_anchor_static(L):
    if L.kind in ("rect", "ellipse", "text"): return (0.0, 0.0)
    return (0.0, 0.0)

def layer_image(L, t, comp):
    """returns (premult RGBA float image, anchor x, anchor y in image px) for layer kind"""
    k = L.kind
    if k == "text":
        img, cx, by = text_raster(val(L.kw["txt"], t), val(L.kw["size"], t), L.kw["weight"], L.kw["color"])
        return img, cx, by
    if k in ("rect", "ellipse"):
        img, cx, cy = shape_raster(L, t); return img, cx, cy
    if k == "image":
        im = load_image(L.kw["path"]); return im, im.shape[1] / 2, im.shape[0] / 2
    if k == "solid":
        w, h = L.kw["w"], L.kw["h"]
        im = np.zeros((h, w, 4), np.float32); im[..., :3] = L.kw["color"]; im[..., 3] = 255
        return im, w / 2, h / 2
    if k == "footage":
        src = video(L.kw.get("seq") or L.kw["path"])
        st = val(L.kw["remap"], t) if L.kw.get("remap") is not None else t - L.kw["start"]
        fps = 30
        im = src.get(int(math.floor(st * fps + 1e-4)))
        return im, im.shape[1] / 2, im.shape[0] / 2
    if k == "precomp":
        c = L.kw["comp"]; im = render_comp(c, t - L.kw["start"], alpha=True)
        return im, c.w / 2, c.h / 2
    raise ValueError(k)

def draw_layer(dst, L, t, comp, alpha_dst=False):
    """track matte support: L.kw['matte'] = a Layer (not added to the comp), L.kw['matte_mode'] = 'alpha' | 'luma'"""
    MT = L.kw.get("matte") if L.kind != "audio" else None
    if MT is None: return _draw_layer(dst, L, t, comp, alpha_dst)
    if not L.enabled or L.guide: return
    if t < L.inp - 1e-6 or (L.outp is not None and t >= L.outp - 1e-6): return
    if val(L.op, t) <= 0.2: return
    buf = np.zeros((comp.h, comp.w, 4), np.float32); _draw_layer(buf, L, t, comp, True)
    mb = np.zeros((comp.h, comp.w, 4), np.float32); _draw_layer(mb, MT, t, comp, True, ignore_time=True)
    m = mb[..., 3] / 255 if L.kw.get("matte_mode", "alpha") == "alpha" else np.clip(mb[..., :3].mean(-1) / 255, 0, 1)
    buf *= m[..., None]
    a = buf[..., 3:4] / 255
    if alpha_dst: dst *= (1 - a); dst += buf
    else: dst *= (1 - a); dst += buf[..., :3]

def _draw_layer(dst, L, t, comp, alpha_dst=False, ignore_time=False):
    if not L.enabled and not ignore_time: return
    if L.guide or L.kind == "audio": return
    if not ignore_time and (t < L.inp - 1e-6 or (L.outp is not None and t >= L.outp - 1e-6)): return
    op = val(L.op, t) / 100
    if op <= 0.002: return
    img, ax, ay = layer_image(L, t, comp)
    if L.anchor is not None:
        an = val(L.anchor, t)
        ax, ay = ax + an[0], ay + an[1]
    s = val(L.scale, t); s = s if not isinstance(s, (list, tuple)) else s[0]
    b = val(L.blur, t)
    if L.shadow:
        img, pad = add_shadow(img, L.shadow, s / 100); ax += pad; ay += pad
    if b > 0.3:
        sig = blur_sigma(b) / max(s / 100, 0.05)
        pad = int(sig * 3) + 1
        img = cv2.copyMakeBorder(img, pad, pad, pad, pad, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))
        img = cv2.GaussianBlur(img, (0, 0), sig); ax += pad; ay += pad
    M = layer_matrix(L, t, ax, ay)
    (rgba_over if alpha_dst else composite)(dst, img, M, op)

def render_comp(comp, t, alpha=False):
    if alpha:
        fr = np.zeros((comp.h, comp.w, 4), np.float32)
    else:
        fr = np.zeros((comp.h, comp.w, 3), np.float32); fr[:] = comp.bg
    for L in comp.layers: draw_layer(fr, L, t, comp, alpha)
    return fr

# ------------------------------------------------------------------ JSX export
def _js(v):
    return json.dumps(v, ensure_ascii=False)

def _col(c): return [round(x / 255, 4) for x in c]

def export_jsx(main, out_path, title, footage_map, extra_comps=()):
    """footage_map: absolute local path -> relative path inside the package"""
    comps = []; seen = set()
    def collect(c):
        for L in c.layers:
            for X in (L, L.kw.get("matte")):
                if X is not None and X.kind == "precomp" and id(X.kw["comp"]) not in seen:
                    collect(X.kw["comp"])
        if id(c) not in seen: seen.add(id(c)); comps.append(c)
    for c in extra_comps: collect(c)
    collect(main)
    lines = []
    w = lines.append
    w("// %s - Palderma\n// يبني مشروع أفترافكت كامل بطبقات وكيفريمات قابلة للتعديل.\n" % title)
    w("// الاستعمال: ثبّت خطوط ثمانية من مجلد fonts، افتح After Effects، File > Scripts > Run Script File... واختار هالملف.\n// لازم يضل الملف جنب مجلدات footage و audio.\n")
    w("#target aftereffects\n(function () {\nvar root = new File($.fileName).parent;\napp.beginUndoGroup(" + _js(title) + ");\nif (!app.project) app.newProject();\nvar proj = app.project;\n")
    w("var top = proj.items.addFolder(" + _js(title + " - Palderma") + ");\nvar fFoot = proj.items.addFolder('Footage'); fFoot.parentFolder = top;\nvar fComp = proj.items.addFolder('مشاهد (Precomps)'); fComp.parentFolder = top;\n")
    w(r'''var cache = {};
function imp(p) { if (cache[p]) return cache[p]; var f = new File(root.fsName + "/" + p);
  if (!f.exists) { alert("الملف مش موجود: " + p); return null; }
  var it = proj.importFile(new ImportOptions(f)); it.parentFolder = fFoot;
  try { if (it.mainSource && it.mainSource.hasAlpha) it.mainSource.guessAlphaMode(); } catch (e) {}
  try { if (it.mainSource && !it.mainSource.isStill) it.mainSource.conformFrameRate = 30; } catch (e) {}
  cache[p] = it; return it; }
function TR(L, m) { return L.property("ADBE Transform Group").property(m); }
function setK(prop, ks, dims, spatial) {
  // ks = [[t, v, inInf, outInf, mode]] mode 0 bezier, 1 linear, 2 hold
  if (ks.length == 1 && ks[0].length == 2) { prop.setValue(ks[0][1]); return; }
  for (var i = 0; i < ks.length; i++) prop.setValueAtTime(ks[i][0], ks[i][1]);
  for (var i = 0; i < ks.length; i++) {
    var k = i + 1, m = ks[i][4];
    if (m == 1) { prop.setInterpolationTypeAtKey(k, KeyframeInterpolationType.LINEAR, KeyframeInterpolationType.LINEAR); continue; }
    if (m == 2) { prop.setInterpolationTypeAtKey(k, KeyframeInterpolationType.HOLD, KeyframeInterpolationType.HOLD); continue; }
    var ei = [], eo = [];
    for (var d = 0; d < dims; d++) { ei.push(new KeyframeEase(0, Math.max(0.1, ks[i][2]))); eo.push(new KeyframeEase(0, Math.max(0.1, ks[i][3]))); }
    try { prop.setTemporalEaseAtKey(k, ei, eo); } catch (e) {}
    if (spatial) { try { prop.setSpatialAutoBezierAtKey(k, false); prop.setSpatialContinuousAtKey(k, false);
      prop.setSpatialTangentsAtKey(k, [0, 0, 0], [0, 0, 0]); } catch (e) {} }
  }
}
function textL(comp, txt, font, size, col) {
  var L = comp.layers.addText(txt); var p = L.property("ADBE Text Properties").property("ADBE Text Document"); var td = p.value;
  try { td.resetCharStyle(); td.resetParagraphStyle(); } catch (e) {}
  td.font = font; td.fontSize = size; td.applyFill = true; td.fillColor = col; td.applyStroke = false; td.tracking = 0;
  td.justification = ParagraphJustification.CENTER_JUSTIFY;
  try { td.paragraphDirection = ParagraphDirection.DIRECTION_RIGHT_TO_LEFT; } catch (e) {}
  p.setValue(td);
  // anchor = ink centre (x) on the baseline (y): editing the word keeps it centred
  TR(L, "ADBE Anchor Point").expression = "var r = sourceRectAtTime(time, false); [r.left + r.width / 2, 0];";
  return L;
}
function textAnchor(L, dx, dy) { TR(L, "ADBE Anchor Point").expression = "var r = sourceRectAtTime(time, false); [r.left + r.width / 2 + (" + dx + "), " + dy + "];"; }
function shapeL(comp, kind, size, radius, fill, fillOp, stroke, strokeW, strokeOp) {
  // add every vector property FIRST, then always re-fetch by match name (adding a property invalidates older references)
  var L = comp.layers.addShape(); L.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group");
  function V() { return L.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group"); }
  V().addProperty(kind == "rect" ? "ADBE Vector Shape - Rect" : "ADBE Vector Shape - Ellipse");
  if (stroke) V().addProperty("ADBE Vector Graphic - Stroke");
  if (fill) V().addProperty("ADBE Vector Graphic - Fill");
  function S() { return V().property(1); }
  function ST() { return V().property("ADBE Vector Graphic - Stroke"); }
  function FL() { return V().property("ADBE Vector Graphic - Fill"); }
  if (stroke) ST().property("ADBE Vector Stroke Color").setValue(stroke);
  if (fill) FL().property("ADBE Vector Fill Color").setValue(fill);
  var r = {
    size: function () { return S().property(kind == "rect" ? "ADBE Vector Rect Size" : "ADBE Vector Ellipse Size"); },
    round: function () { return S().property("ADBE Vector Rect Roundness"); },
    sw: function () { return ST().property("ADBE Vector Stroke Width"); },
    sop: function () { return ST().property("ADBE Vector Stroke Opacity"); },
    fop: function () { return FL().property("ADBE Vector Fill Opacity"); }
  };
  TR(L, "ADBE Anchor Point").setValue([0, 0]);
  return [L, r];
}
var ERRS = [];
''')
    names = {}
    for ci, c in enumerate(comps):
        cv = "C%d" % ci; names[id(c)] = cv
        w("var %s = proj.items.addComp(%s, %d, %d, 1, %s, %s); %s.parentFolder = %s; %s.bgColor = %s;\n" % (
            cv, _js(c.name), c.w, c.h, _js(round(c.dur, 4)), c.fps, cv, "top" if c is main else "fComp", cv, _js(_col(c.bg))))
        for t, txt in c.markers:
            w("try { var mk = new MarkerValue(%s); %s.markerProperty.setValueAtTime(%s, mk); } catch (e) {}\n" % (_js(txt), cv, _js(round(t, 3))))
        for L in c.layers:
            w("try {\n"); _jsx_layer(w, L, c, cv, names, footage_map)
            MT = L.kw.get("matte")
            if MT is not None:
                w("var ML = L;\n"); _jsx_layer(w, MT, c, cv, names, footage_map)
                tm = "ALPHA" if L.kw.get("matte_mode", "alpha") == "alpha" else "LUMA"
                w("var MT = L; try { ML.setTrackMatte(MT, TrackMatteType.%s); } catch (e) { ML.trackMatteType = TrackMatteType.%s; }\nL = ML;\n" % (tm, tm))
            w("} catch (err) { ERRS.push(%s + ': ' + err.toString() + ' (line ' + err.line + ')'); }\n" % _js(c.name + " / " + L.name))
    w("app.endUndoGroup();\n%s.openInViewer();\nif (ERRS.length) alert('انبنى المشروع، بس في طبقات ما زبطت (ابعت صورة عن هالرسالة):\\n' + ERRS.slice(0, 15).join('\\n')); else alert(%s);\n})();\n" % (names[id(main)], _js("تمام! انبنى مشروع «" + title + "» بكل الطبقات والكيفريمات.")))
    open(out_path, "w", encoding="utf-8-sig").write("".join(lines))

def _kjs(p, conv=lambda v: v):
    if not animated(p): return [[0, conv(p)]]
    out = []
    for k in p:
        mode = 2 if k.hold else (1 if k.lin else 0)
        out.append([round(k.t, 4), conv(k.v), k.i, k.o, mode])
    return out

def _jsx_layer(w, L, c, cv, names, fmap):
    k = L.kind; lv = "L"
    if k == "text":
        w("var L = textL(%s, %s, %s, %s, %s);\n" % (cv, _js(L.kw["txt"]), _js(FONT_PS[L.kw["weight"]]), _js(L.kw["size"]), _js(_col(L.kw["color"]))))
    elif k in ("rect", "ellipse"):
        w("var SR = shapeL(%s, %s, [10,10], 0, %s, 100, %s, 1, 100); var L = SR[0];\n" % (
            cv, _js(k), _js(_col(L.kw["fill"])) if L.kw.get("fill") is not None else "null", _js(_col(L.kw["stroke"])) if L.kw.get("stroke") else "null"))
        w("setK(SR[1].size(), %s, 2, false);\n" % _js(_kjs(L.kw["size"])))
        if k == "rect": w("setK(SR[1].round(), %s, 1, false);\n" % _js(_kjs(L.kw["radius"])))
        if L.kw.get("fill") is not None: w("setK(SR[1].fop(), %s, 1, false);\n" % _js(_kjs(L.kw.get("fill_op", 100))))
        if L.kw.get("stroke"):
            w("setK(SR[1].sw(), %s, 1, false); setK(SR[1].sop(), %s, 1, false);\n" % (_js(_kjs(L.kw["stroke_w"])), _js(_kjs(L.kw.get("stroke_op", 100)))))
    elif k in ("image", "footage", "audio"):
        rel = fmap[L.kw["path"]]
        w("var L = %s.layers.add(imp(%s));\n" % (cv, _js(rel)))
        if k in ("footage", "audio"):
            w("L.startTime = %s;\n" % _js(round(L.kw["start"], 4)))
            if L.kw.get("remap") is not None:
                w("L.timeRemapEnabled = true; var RM = L.property('ADBE Time Remapping'); try { while (RM.numKeys > 1) RM.removeKey(RM.numKeys); } catch (e) {}\nsetK(RM, %s, 1, false);\ntry { if (RM.numKeys > 0 && RM.keyTime(RM.numKeys) > %s) RM.removeKey(RM.numKeys); } catch (e) {}\n" % (_js(_kjs(L.kw["remap"])), _js(round(L.kw["remap"][-1].t + 0.01, 3))))
    elif k == "precomp":
        w("var L = %s.layers.add(%s); L.startTime = %s;\n" % (cv, names[id(L.kw["comp"])], _js(round(L.kw["start"], 4))))
    elif k == "solid":
        w("var L = %s.layers.addSolid(%s, %s, %d, %d, 1);\n" % (cv, _js(_col(L.kw["color"])), _js(L.name), L.kw["w"], L.kw["h"]))
    w("L.name = %s;\n" % _js(L.name))
    if L.comment: w("L.comment = %s;\n" % _js(L.comment))
    # in / out (layers stay in stacking order: each new layer goes on top)
    outp = L.outp if L.outp is not None else c.dur
    w("try { L.inPoint = %s; L.outPoint = %s; } catch (e) {}\n" % (_js(round(max(0, L.inp), 4)), _js(round(min(outp, c.dur), 4))))
    if k in ("rect", "ellipse", "text"):
        if L.anchor is not None and k == "text": w("textAnchor(L, %s, %s);\n" % (val(L.anchor, 0)[0], val(L.anchor, 0)[1]))
        if L.anchor is not None and k != "text": w("setK(TR(L,'ADBE Anchor Point'), %s, 2, false);\n" % _js(_kjs(L.anchor)))
    elif L.anchor is not None:
        w("var AP = TR(L,'ADBE Anchor Point'); AP.setValue([AP.value[0] + %s, AP.value[1] + %s]);\n" % (val(L.anchor, 0)[0], val(L.anchor, 0)[1]))
    if k == "audio":
        if L.kw.get("audio_off"): w("try { L.audioEnabled = false; } catch (e) {}\n")
        return
    sc = L.scale
    conv_s = (lambda v: [v, v]) if not isinstance(val(sc, 0), (list, tuple)) else (lambda v: list(v))
    w("setK(TR(L,'ADBE Position'), %s, 1, true);\n" % _js(_kjs(L.pos, lambda v: [round(v[0], 2), round(v[1], 2)])))
    w("setK(TR(L,'ADBE Scale'), %s, 2, false);\n" % _js(_kjs(sc, lambda v: [round(x, 3) for x in conv_s(v)])))
    if animated(L.rot) or L.rot: w("setK(TR(L,'ADBE Rotate Z'), %s, 1, false);\n" % _js(_kjs(L.rot)))
    w("setK(TR(L,'ADBE Opacity'), %s, 1, false);\n" % _js(_kjs(L.op)))
    if L.shadow:
        sh = L.shadow
        w("var DS = L.property('ADBE Effect Parade').addProperty('ADBE Drop Shadow'); try { DS.property(1).setValue(%s); DS.property(2).setValue(%s); DS.property(3).setValue(%s); DS.property(4).setValue(%s); DS.property(5).setValue(%s);} catch (e) {}\n" % (
            _js(_col(sh.get("color", (40, 3, 15)))), sh.get("op", 128), sh.get("dir", 180), sh.get("dist", 6), sh.get("soft", 20)))
    if animated(L.blur) or L.blur:
        w("var GB = L.property('ADBE Effect Parade').addProperty('ADBE Gaussian Blur 2'); try { GB.property('ADBE Gaussian Blur 2-0003').setValue(1); } catch (e) {}\nsetK(GB.property(1), %s, 1, false);\n" % _js(_kjs(L.blur)))
    if L.parent is not None:
        w("// parent set below\n")
    if L.guide: w("L.guideLayer = true;\n")
    if not L.enabled: w("L.enabled = false;\n")
    if L.kw.get("audio_off"): w("try { L.audioEnabled = false; } catch (e) {}\n")
