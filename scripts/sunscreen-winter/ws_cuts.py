"""cut list for «ضرورة واقي الشمس بالشتاء»: only long pauses removed; every join is a 6-frame soft cross-dissolve"""
SRC = "/mnt/project-files/ضرورة واقي الشمس بالشتاء.mp4"
FPS = 30; XF = 6                                     # crossfade frames at each join
# v3: no cut inside a card glide or the hook (pauses kept there so the doctor never "jumps")
KEEP_F = [(32, 253), (263, 411), (419, 602), (619, 810), (818, 1216), (1223, 1331)]
KEEP = [(a / FPS, b / FPS) for a, b in KEEP_F]
STARTS = []; _acc = 0
for k, (a, b) in enumerate(KEEP_F):
    STARTS.append(_acc); _acc += (b - a) - XF
DOC_FRAMES = _acc + XF
DOC_LEN = DOC_FRAMES / FPS
CUTS = [round((STARTS[k] + XF / 2) / FPS, 4) for k in range(1, len(KEEP_F))]   # centre of each dissolve (timeline s)
def o(r):
    """raw seconds -> timeline seconds (later segment wins inside a dissolve)"""
    f = r * FPS
    for k in range(len(KEEP_F) - 1, -1, -1):
        a, b = KEEP_F[k]
        if f >= a: return round((STARTS[k] + min(f, b) - a) / FPS, 4)
    return 0.0
