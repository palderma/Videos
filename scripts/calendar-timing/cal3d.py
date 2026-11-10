#!/usr/bin/env python3
"""2.5D/3D calendar renderer: perspective camera, wire-o binding, bending page flips with lighting,
cast shadows on the stack and on the wall, motion blur by sub-frame accumulation.
Writes straight-alpha RGBA PNG frames (calendar + its shadows) for the compositor and for After Effects.
usage: cal3d.py <out_dir> <f0> <f1> [--t=sec]"""
import sys, os, math
import numpy as np, cv2
from PIL import Image
from tl import *
import textures as TX

PW, PH = TX.PW, TX.PH
HY = 372.0                        # hinge line (local y)
BTOP, BBOT = HY + 4, HY + 4 - TX.BH
BZF, BZB = -11.0, -27.0           # board front / back
RING_R, RING_ZC = 15.0, -3.0
F = 2350.0; CX0, CY0 = 540.0, 830.0
LIGHT = np.array([-0.42, 0.55, 0.72]); LIGHT /= np.linalg.norm(LIGHT)
LPOS = np.array([-1300.0, 1700.0, 2400.0])     # point light for cast shadows (local space)

def rot(rx, ry, rz=0.0):
    rx, ry, rz = map(math.radians, (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Ry = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Rz = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Ry @ Rx @ Rz

# ------------------------------------------------------------------ choreography
def cal_xf(t):
    """calendar transform: (R, T) local -> world, plus camera distance and DOF blur"""
    e = seg(t, 0.0, 2.1, 0.10, 0.92)                       # entrance: rise from below, tilt settles
    ty = lerp(-560, 0, e); tz = lerp(-1900, 0, e)
    rx = lerp(42, 4, seg(t, 0.0, 2.3, 0.10, 0.90))
    ry = lerp(-26, -9, seg(t, 0.0, 2.5, 0.10, 0.85))
    rz = lerp(-5, 0, seg(t, 0.0, 2.2, 0.1, 0.9))
    # living drift (very slow)
    ry += 3.2 * math.sin(2 * math.pi * (t - 2.0) / 13.0) * clamp((t - 1.2) / 1.5)
    rx += 1.2 * math.sin(2 * math.pi * (t - 1.0) / 9.0) * clamp((t - 1.2) / 1.5)
    # gentle push-ins after each page settles, released before the next flip
    push = 0.0
    for a, b, c, d in ((3.3, 5.6, 5.7, 6.4), (6.6, 8.6, 8.75, 9.4), (9.7, 11.6, 11.75, 12.3)):
        push += 70 * seg(t, a, b, 0.4, 0.6) - 70 * seg(t, c, d, 0.5, 0.5) * (t >= c)
    tz += push
    # ending: calendar recedes and floats up, turning a touch
    fe = seg(t, 12.25, 13.55, 0.55, 0.80)
    ty += lerp(0, 215, fe); tz += lerp(0, -1060, fe); ry += lerp(0, -7, fe); rx += lerp(0, 3, fe)
    blur = 14 * (1 - seg(t, 0.0, 1.7, 0.2, 0.8))
    return rot(rx, ry, rz), np.array([0.0, ty, tz]), blur

CAM = np.array([0.0, 0.0, 2050.0])
def project(Pw):
    """world -> screen; camera at CAM looking down -z"""
    d = CAM[2] - Pw[..., 2]
    d = np.maximum(d, 30.0)
    x = CX0 + F * (Pw[..., 0] - CAM[0]) / d
    y = CY0 - F * (Pw[..., 1] - CAM[1]) / d
    return np.stack([x, y], -1), d

# ------------------------------------------------------------------ page flip geometry
NV, NU = 56, 5
def flip_angles(p):
    """tangent angle at hinge (top) and at the free edge (bottom), degrees; the bottom leads -> curl"""
    END = 300.0
    bot = END * bez(clamp(p / 0.80), 0.30, 0.55)
    top = END * bez(clamp((p - 0.10) / 0.90), 0.55, 0.45)
    return top, bot

def page_grid(p, zp, twist_dir=1.0):
    """local 3D grid (NV+1, NU+1, 3) of a page at flip progress p (0 = hanging flat)"""
    s = np.linspace(0, 1, NV + 1)[:, None]
    u = np.linspace(0, 1, NU + 1)[None, :]
    top, bot = flip_angles(p)
    phi = top + (bot - top) * s ** 1.55
    # leading corner (bottom right) + damped flutter
    tw = 22 * math.sin(math.pi * clamp(p / 0.85)) * twist_dir
    phi = phi + tw * (u - 0.5) * 2 * s ** 1.8
    phi = phi + 4 * math.sin(math.pi * clamp(p / 0.9)) * np.sin(s * 5.0 - p * 9)
    ph = np.radians(phi)
    dy = -np.cos(ph); dz = np.sin(ph)
    ds = PH / NV
    y = HY + np.concatenate([np.zeros((1, NU + 1)), np.cumsum((dy[1:] + dy[:-1]) / 2 * ds, 0)], 0)
    z = zp + np.concatenate([np.zeros((1, NU + 1)), np.cumsum((dz[1:] + dz[:-1]) / 2 * ds, 0)], 0)
    x = np.broadcast_to(-PW / 2 + u * PW, y.shape)
    return np.stack([x, y, z], -1)

def flat_grid(zp):
    s = np.linspace(0, 1, 2)[:, None]; u = np.linspace(0, 1, 2)[None, :]
    x = np.broadcast_to(-PW / 2 + u * PW, (2, 2)); y = np.broadcast_to(HY - s * PH, (2, 2))
    return np.stack([x, y, np.full((2, 2), zp)], -1)

def normals(G):
    """per-vertex normal of the FRONT face (local)"""
    ds = np.gradient(G, axis=0); du = np.gradient(G, axis=1)
    n = np.cross(ds, du)            # front: s goes down, u goes right -> (down x right) = +z for flat page
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-9
    return n

# ------------------------------------------------------------------ rasteriser
def draw_tex_quad(buf, tex, src4, dst4, expand=0.6):
    """premultiplied over of a texture quad (homography) into buf (premult RGBA float)"""
    c = dst4.mean(0)
    v = dst4 - c; L = np.linalg.norm(v, axis=1, keepdims=True) + 1e-6
    de = dst4 + v / L * expand
    x0, y0 = np.floor(de.min(0)).astype(int); x1, y1 = np.ceil(de.max(0)).astype(int) + 1
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, buf.shape[1]), min(y1, buf.shape[0])
    if x1 - x0 < 1 or y1 - y0 < 1: return
    a_, b_ = dst4[2] - dst4[0], dst4[3] - dst4[1]
    area = abs(a_[0] * b_[1] - a_[1] * b_[0]) / 2
    if area < 0.3: return
    Hm = cv2.getPerspectiveTransform(src4.astype(np.float32), (dst4 - [x0, y0]).astype(np.float32))
    wp = cv2.warpPerspective(tex, Hm, (x1 - x0, y1 - y0), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillConvexPoly(m, np.round((de - [x0, y0]) * 16).astype(np.int32), 255, cv2.LINE_AA, 4)
    m = m.astype(np.float32)[..., None] / 255
    s = wp * m
    sub = buf[y0:y1, x0:x1]
    sub *= (1 - s[..., 3:4] / 255); sub += s

def draw_poly(buf, pts, col, alpha=1.0):
    pts = np.asarray(pts, np.float64)
    x0, y0 = np.floor(pts.min(0)).astype(int) - 1; x1, y1 = np.ceil(pts.max(0)).astype(int) + 2
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, buf.shape[1]), min(y1, buf.shape[0])
    if x1 - x0 < 1 or y1 - y0 < 1: return
    m = np.zeros((y1 - y0, x1 - x0), np.uint8)
    cv2.fillConvexPoly(m, np.round((pts - [x0, y0]) * 16).astype(np.int32), 255, cv2.LINE_AA, 4)
    a = m.astype(np.float32)[..., None] / 255 * alpha
    sub = buf[y0:y1, x0:x1]
    sub *= (1 - a); sub[..., :3] += np.array(col, np.float32) * a; sub[..., 3:4] += 255 * a

def shade_vals(Nw, Pw, back=False):
    """lighting multiplier + specular for world normals/positions (front face unless back)"""
    n = -Nw if back else Nw
    V = CAM - Pw; V /= np.linalg.norm(V, axis=-1, keepdims=True)
    nd = np.clip((n * LIGHT).sum(-1), 0, 1)
    Hh = LIGHT + V; Hh /= np.linalg.norm(Hh, axis=-1, keepdims=True)
    sp = np.clip((n * Hh).sum(-1), 0, 1) ** 36
    # flat page facing camera ~= 1.0
    flat = 0.62 + 0.42 * LIGHT[2]
    k = (0.62 + 0.42 * nd) / flat
    # softly darker when the sheet turns away from the camera (grazing)
    face = np.abs((n * V).sum(-1))
    k *= 0.80 + 0.20 * np.clip(face * 1.6, 0, 1)
    if back: k = 0.80 + 0.22 * k
    return k, sp

def shaded(tex, k_grid, sp_grid, spec_col=(255, 236, 242), spec_amt=70):
    h, w = tex.shape[:2]
    k = cv2.resize(k_grid.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
    s = cv2.resize(sp_grid.astype(np.float32), (w, h), interpolation=cv2.INTER_LINEAR)
    out = tex.copy()
    a = out[..., 3:4] / 255
    out[..., :3] *= k[..., None]
    out[..., :3] += (s[..., None] * spec_amt) * np.array(spec_col, np.float32) / 255 * a
    np.clip(out, 0, 255, out=out)
    out[..., :3] = np.minimum(out[..., :3], out[..., 3:4])
    return out

def tex_src(tex, iu0, iu1, iv0, iv1, nu, nv):
    h, w = tex.shape[:2]
    TWp, THp = w - 4, h - 4
    xs = [2 + TWp * iu0 / nu, 2 + TWp * iu1 / nu]; ys = [2 + THp * iv0 / nv, 2 + THp * iv1 / nv]
    return np.array([[xs[0], ys[0]], [xs[1], ys[0]], [xs[1], ys[1]], [xs[0], ys[1]]], np.float32)

# ------------------------------------------------------------------ calendar frame
def page_state(name, t):
    if name in FLIPS:
        t0, d = FLIPS[name]
        if t >= t0 + d: return None
        if t >= t0: return (t - t0) / d
    return 0.0

def bar_fill(name, t):
    if name in SETTLE: return seg(t, SETTLE[name], SETTLE[name] + 1.05, 0.35, 0.75)
    return 1.0

def render_sub(t):
    R, T, blur = cal_xf(t)
    def W_(P): return P @ R.T + T
    buf = np.zeros((H, W, 4), np.float32)

    # ---- wall shadow + contact shadow (soft, lower-right), drawn at 1/4 res
    q = 4
    sm = np.zeros((H // q, W // q), np.float32)
    corners = np.array([[-TX.BW / 2, BTOP, BZB], [TX.BW / 2, BTOP, BZB], [TX.BW / 2, BBOT, BZB], [-TX.BW / 2, BBOT, BZB]])
    for zw, a_, sg in ((-190.0, 0.50, 34), (-60.0, 0.30, 12)):
        pts = []
        for c in corners:
            k = (LPOS[2] - zw) / (LPOS[2] - c[2]); pts.append(LPOS + (c - LPOS) * k)
        sp, _ = project(W_(np.array(pts)))
        m = np.zeros_like(sm)
        cv2.fillConvexPoly(m, np.round(sp / q * 16).astype(np.int32), 1.0, cv2.LINE_AA, 4)
        sm = np.maximum(sm, cv2.GaussianBlur(m, (0, 0), sg / q) * a_)
    sm = cv2.resize(sm, (W, H), interpolation=cv2.INTER_LINEAR)
    buf[..., 3] = sm * 255 * 0.85          # black shadow (premult rgb stays 0)
    buf[..., :3] = 0

    # pages: which are on screen
    states = [(nm, page_state(nm, t)) for nm in PAGES]
    live = [(nm, p) for nm, p in states if p is not None]
    static = next(nm for nm, p in live if p == 0.0)
    flipping = [(nm, p) for nm, p in live if p > 0.0]
    nstatic = PAGES.index(static)

    # ---- rings (back half), drawn before everything
    ring_pts = ring_geometry()
    ring_draw(buf, ring_pts, W_, front=False)

    # ---- flipping pages: geometry and per-cell splitting into behind/front passes
    cells_behind, cells_front, shadow_src = [], [], []
    for i, (nm, p) in enumerate(flipping):
        zp = 0.9 * (len(flipping) - 1 - i) * 0.0 + 0.6 * (len(flipping) - i)
        G = page_grid(p, zp, 1.0)
        Gw = W_(G.reshape(-1, 3)).reshape(G.shape)
        Nl = normals(G); Nw = Nl @ R.T
        S, D = project(Gw)
        kf, spf = shade_vals(Nw, Gw); kb, spb = shade_vals(Nw, Gw, back=True)
        tf = shaded(TX.page_tex(nm, bar_fill(nm, t)), kf, spf)
        tb = shaded(TX.back_tex(nm), kb, spb, spec_amt=40)
        # cells
        cen = (Gw[:-1, :-1] + Gw[1:, 1:]) / 2
        Vc = CAM - cen
        nc = (Nw[:-1, :-1] + Nw[1:, 1:]) / 2
        front = (nc * Vc).sum(-1) > 0
        Gl_c = (G[:-1, :-1] + G[1:, 1:]) / 2
        depth = (D[:-1, :-1] + D[1:, 1:]) / 2
        for iv in range(NV):
            for iu in range(NU):
                dst = np.array([S[iv, iu], S[iv, iu + 1], S[iv + 1, iu + 1], S[iv + 1, iu]])
                tex = tf if front[iv, iu] else tb
                src = tex_src(tex, iu, iu + 1, iv, iv + 1, NU, NV)
                cell = (depth[iv, iu] - i * 1e-3, tex, src, dst)
                (cells_behind if Gl_c[iv, iu, 2] < BZF - 2 else cells_front).append(cell)
        shadow_src.append(G)

    for c in sorted(cells_behind, key=lambda c: -c[0]):
        draw_tex_quad(buf, c[1], c[2], c[3])

    # ---- board: sides then front
    bw2 = TX.BW / 2
    box = {
        "front": [[-bw2, BTOP, BZF], [bw2, BTOP, BZF], [bw2, BBOT, BZF], [-bw2, BBOT, BZF]],
        "left": [[-bw2, BTOP, BZB], [-bw2, BTOP, BZF], [-bw2, BBOT, BZF], [-bw2, BBOT, BZB]],
        "right": [[bw2, BTOP, BZF], [bw2, BTOP, BZB], [bw2, BBOT, BZB], [bw2, BBOT, BZF]],
        "bottom": [[-bw2, BBOT, BZF], [bw2, BBOT, BZF], [bw2, BBOT, BZB], [-bw2, BBOT, BZB]],
        "top": [[-bw2, BTOP, BZB], [bw2, BTOP, BZB], [bw2, BTOP, BZF], [-bw2, BTOP, BZF]],
    }
    nrm = {"left": [-1, 0, 0], "right": [1, 0, 0], "bottom": [0, -1, 0], "top": [0, 1, 0], "front": [0, 0, 1]}
    for side in ("left", "right", "bottom", "top"):
        P = W_(np.array(box[side], float)); n = np.array(nrm[side]) @ R.T
        if (n * (CAM - P.mean(0))).sum() <= 0: continue
        k = 0.45 + 0.35 * max(0, (n * LIGHT).sum())
        sp, _ = project(P)
        draw_poly(buf, sp, (205 * k + 20, 160 * k + 14, 172 * k + 16))
    P = W_(np.array(box["front"], float)); sp, _ = project(P)
    bt = TX.board_tex(); h_, w_ = bt.shape[:2]
    draw_tex_quad(buf, bt, np.array([[2, 2], [w_ - 2, 2], [w_ - 2, h_ - 2], [2, h_ - 2]], np.float32), sp, expand=0.0)

    # ---- page stack (remaining sheets): side + bottom edges
    nleft = len(PAGES) - nstatic
    zt = 0.0; zb = BZF + 0.5
    thick = min(1.0, 0.35 + 0.13 * nleft)
    zt = zb + (0 - zb) * thick
    pw2 = PW / 2; yb = HY - PH
    edges = {
        "right": ([[pw2, HY, zt], [pw2, HY, zb], [pw2, yb, zb], [pw2, yb, zt]], [1, 0, 0]),
        "left": ([[-pw2, HY, zb], [-pw2, HY, zt], [-pw2, yb, zt], [-pw2, yb, zb]], [-1, 0, 0]),
        "bottom": ([[-pw2, yb, zt], [pw2, yb, zt], [pw2, yb, zb], [-pw2, yb, zb]], [0, -1, 0]),
    }
    et = TX.edge_tex(9)
    for side, (pts, n) in edges.items():
        P = W_(np.array(pts, float)); nw = np.array(n) @ R.T
        if (nw * (CAM - P.mean(0))).sum() <= 0: continue
        sp, _ = project(P)
        kk = 0.78 + 0.25 * max(0, (nw * LIGHT).sum())
        e2 = et.copy(); e2[..., :3] *= kk
        hh = et.shape[0]
        src = np.array([[0, 0], [8, 0], [8, hh], [0, hh]], np.float32)
        if side == "bottom": src = np.array([[0, 0], [8, 0], [8, hh], [0, hh]], np.float32)
        else: src = np.array([[0, 0], [0, hh], [8, hh], [8, 0]], np.float32)[[0, 1, 2, 3]]
        # sheets run along the long edge: map texture rows across the thickness
        if side == "bottom": draw_tex_quad(buf, e2, np.array([[0, 0], [8, 0], [8, hh], [0, hh]], np.float32), sp)
        else: draw_tex_quad(buf, np.ascontiguousarray(np.transpose(e2, (1, 0, 2))), np.array([[0, 0], [hh, 0], [hh, 8], [0, 8]], np.float32) if side == "left" else np.array([[0, 0], [hh, 0], [hh, 8], [0, 8]], np.float32), sp)

    # ---- static top page (flat)
    G = flat_grid(zt)
    Gw = W_(G.reshape(-1, 3)).reshape(G.shape)
    S, _ = project(Gw)
    Nw = np.broadcast_to(np.array([0, 0, 1.0]) @ R.T, G.shape)
    k, sp = shade_vals(Nw, Gw)
    tex = shaded(TX.page_tex(static, bar_fill(static, t)), k, sp)
    draw_tex_quad(buf, tex, tex_src(tex, 0, 1, 0, 1, 1, 1), np.array([S[0, 0], S[0, 1], S[1, 1], S[1, 0]]))

    # ---- cast shadow of the lifting pages onto the stack (point light projection onto z = zt)
    if shadow_src:
        q2 = 2
        shm = np.zeros((H // q2, W // q2), np.float32); shm2 = np.zeros_like(shm)
        for G in shadow_src:
            Pz = G.reshape(-1, 3)
            h_ = np.maximum(Pz[:, 2] - zt, 0)
            k = (LPOS[2] - zt) / np.maximum(LPOS[2] - Pz[:, 2], 1)
            Q = LPOS + (Pz - LPOS) * k[:, None]; Q[:, 2] = zt
            sp, _ = project(W_(Q)); sp = sp.reshape(G.shape[0], G.shape[1], 2)
            hh = h_.reshape(G.shape[:2])
            for iv in range(0, NV, 2):
                for iu in range(NU):
                    pts = np.array([sp[iv, iu], sp[iv, iu + 1], sp[min(iv + 2, NV), iu + 1], sp[min(iv + 2, NV), iu]]) / q2
                    hv = hh[iv:iv + 3, iu:iu + 2].mean()
                    tgt = shm if hv < 90 else shm2
                    a = 0.55 * math.exp(-hv / 520)
                    m = np.zeros_like(shm)
                    cv2.fillConvexPoly(m, np.round(pts * 16).astype(np.int32), 1.0, cv2.LINE_AA, 4)
                    np.maximum(tgt, m * a, out=tgt)
        sh = cv2.GaussianBlur(shm, (0, 0), 5) + cv2.GaussianBlur(shm2, (0, 0), 16)
        sh = cv2.resize(np.clip(sh, 0, 0.6), (W, H), interpolation=cv2.INTER_LINEAR)
        # only darken the calendar itself (not the wall shadow area)
        cover = np.clip(buf[..., 3] / 255 - sm * 0.85, 0, 1)
        buf[..., :3] *= (1 - sh * cover)[..., None]
        # tint the shadow very slightly wine
        buf[..., 0] += (sh * cover) * 6 * (buf[..., 3] / 255)

    for c in sorted(cells_front, key=lambda c: -c[0]):
        draw_tex_quad(buf, c[1], c[2], c[3])

    ring_draw(buf, ring_pts, W_, front=True)
    return buf, blur

# ------------------------------------------------------------------ wire-o rings
def ring_geometry():
    th = np.linspace(0, 2 * np.pi, 41)
    out = []
    for x in TX.RING_X:
        for dx in (-4.2, 4.2):
            y = HY - 1.0 + RING_R * np.cos(th) * 0.95
            z = RING_ZC + RING_R * np.sin(th)
            out.append(np.stack([np.full_like(th, x + dx), y, z], -1))
    return out

def ring_draw(buf, rings, W_, front):
    S2 = 2
    allp = []
    segs = []
    for r in rings:
        Pw = W_(r)
        sp, _ = project(Pw)
        for i in range(len(r) - 1):
            zc = (r[i, 2] + r[i + 1, 2]) / 2
            if (zc > RING_ZC + 0.5) != front: continue
            # wire normal ~ radial direction in y-z
            nl = np.array([0, (r[i, 1] + r[i + 1, 1]) / 2 - (HY - 1), zc - RING_ZC]); nl /= np.linalg.norm(nl) + 1e-9
            segs.append((sp[i], sp[i + 1], nl))
            allp += [sp[i], sp[i + 1]]
    if not segs: return
    allp = np.array(allp)
    x0, y0 = np.floor(allp.min(0)).astype(int) - 6; x1, y1 = np.ceil(allp.max(0)).astype(int) + 6
    x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W), min(y1, H)
    if x1 <= x0 or y1 <= y0: return
    w, h = (x1 - x0) * S2, (y1 - y0) * S2
    col = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), np.uint8)
    o = np.array([x0, y0])
    def P(p): return tuple(np.round((p - o) * S2 * 8).astype(int))
    th = max(2, int(round(3.6 * S2)))
    for p, q_, nl in segs:
        cv2.line(a, P(p), P(q_), 255, th + 2, cv2.LINE_AA, 3)
    for p, q_, nl in segs:
        cv2.line(col, P(p), P(q_), (96, 52, 58), th + 2, cv2.LINE_AA, 3)
    for p, q_, nl in segs:
        d = max(0.0, float(nl @ LIGHT))
        base = np.array([214, 160, 150]) * (0.55 + 0.6 * d)
        cv2.line(col, P(p), P(q_), tuple(float(c) for c in np.clip(base, 0, 255)), th, cv2.LINE_AA, 3)
    for p, q_, nl in segs:
        d = max(0.0, float(nl @ LIGHT))
        if d > 0.55:
            off = np.array([-0.6, -0.6])
            cv2.line(col, P(p + off), P(q_ + off), (255, 236, 228), max(1, th // 3), cv2.LINE_AA, 3)
    col = cv2.resize(col, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA).astype(np.float32)
    af = cv2.resize(a, (x1 - x0, y1 - y0), interpolation=cv2.INTER_AREA).astype(np.float32)[..., None] / 255
    sub = buf[y0:y1, x0:x1]
    # col was drawn on black: un-premultiply-ish by using coverage as alpha
    sub *= (1 - af); sub[..., :3] += col * af / np.maximum(af, 1e-3) * af; sub[..., 3:4] += 255 * af

# ------------------------------------------------------------------ frame with motion blur
def moving(t):
    if t < 2.2: return True
    for nm, (t0, d) in FLIPS.items():
        if t0 - 0.05 <= t <= t0 + d + 0.05: return True
    if 12.2 <= t <= 13.6: return True
    return False

def render_frame(fi):
    t = fi / FPS
    if moving(t):
        n = 12 if any(t0 - 0.05 <= t <= t0 + d + 0.05 for t0, d in FLIPS.values()) else 6
        acc = np.zeros((H, W, 4), np.float32); bl = 0
        for j in range(n):
            b, bl = render_sub(t + (j / n - 0.5) * 0.5 / FPS)
            acc += b
        buf = acc / n
    else:
        buf, bl = render_sub(t)
    if bl > 0.3:
        buf = cv2.GaussianBlur(buf, (0, 0), bl)
    return buf

def save(buf, path):
    a = buf[..., 3:4]
    rgb = np.where(a > 0.5, buf[..., :3] * 255 / np.maximum(a, 1e-3), 0)
    out = np.dstack([np.clip(rgb, 0, 255), np.clip(a, 0, 255)]).astype(np.uint8)
    cv2.imwrite(path, cv2.cvtColor(out, cv2.COLOR_RGBA2BGRA), [cv2.IMWRITE_PNG_COMPRESSION, 1])

if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    ts = [a for a in sys.argv if a.startswith("--t=")]
    if ts:
        for tv in ts[0][4:].split(","):
            fi = int(round(float(tv) * FPS))
            save(render_frame(fi), os.path.join(out, "t%05d.png" % fi))
        sys.exit()
    f0, f1 = int(sys.argv[2]), int(sys.argv[3])
    for fi in range(f0, f1):
        p = os.path.join(out, "c%05d.png" % fi)
        if os.path.exists(p): continue
        save(render_frame(fi), p)
