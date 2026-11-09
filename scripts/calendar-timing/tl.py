"""Timeline for «التوقيت قبل المناسبة» calendar motion (shared by calendar render, compositor and audio)."""
import math
W, H, FPS, DUR = 1080, 1920, 30, 15.0
NF = int(round(DUR * FPS))

BURG = (108, 13, 43); PINK = (243, 165, 189); WHITE = (255, 255, 255)

# pages in stack order (top first)
PAGES = ["cover", "4", "3", "2", "1", "event"]
# flip start / duration for each page that gets turned
FLIPS = {"cover": (2.80, 0.95), "4": (5.70, 0.80), "3": (6.08, 0.74), "2": (8.80, 1.05), "1": (11.80, 0.95)}
# when each numbered page has settled (bars fill)
SETTLE = {"4": 3.50, "2": 6.75, "1": 9.80}
FILLED = {"4": 4, "3": 3, "2": 2, "1": 1}

# text scenes: (line1 runs, pill text, t_in, t_out)   runs = [(text, pink?)] in reading order (RTL)
SCENES = [
    dict(l1=[("عندك", 0), ("مناسبة؟", 1)], l2=[("كم", 0), ("أسبوع", 0), ("باقي؟", 0)], pill=False, tin=0.10, tin2=0.62, tout=2.62),
    dict(l1=[("قبل", 0), ("4 أسابيع", 1)], l2="ابدأ بالاستشارة", pill=True, tin=3.35, tin2=3.72, tout=5.62),
    dict(l1=[("قبل", 0), ("أسبوعين", 1)], l2="آخر موعد لأي خطوة جديدة", pill=True, tin=6.62, tin2=6.98, tout=8.72),
    dict(l1=[("قبل", 0), ("أسبوع", 1)], l2="عناية لطيفة فقط", pill=True, tin=9.62, tin2=9.98, tout=11.68),
]
FINAL = dict(runs=[("التوقيت", 0), ("بيفرق", 1)], tin=12.70, logo=13.30)
FRAME_OUT = (12.15, 12.75)     # brand frame fades for the clean ending

def clamp(x, a=0.0, b=1.0): return a if x < a else b if x > b else x

def bez(x, o=0.75, n=0.75):
    """AE temporal ease: bezier (0,0),(o,0),(1-n,1),(1,1)"""
    if x <= 0: return 0.0
    if x >= 1: return 1.0
    x1, x2 = o, 1 - n; lo, hi = 0.0, 1.0
    for _ in range(36):
        u = (lo + hi) / 2
        bx = 3 * (1 - u) ** 2 * u * x1 + 3 * (1 - u) * u * u * x2 + u ** 3
        if bx < x: lo = u
        else: hi = u
    u = (lo + hi) / 2
    return 3 * (1 - u) * u * u + u ** 3

def seg(t, t0, t1, o=0.75, n=0.75): return bez((t - t0) / (t1 - t0), o, n)
def lerp(a, b, k): return a + (b - a) * k
