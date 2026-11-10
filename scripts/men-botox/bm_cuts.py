"""cut list for «بوتوكس الرجال»: only the lead-in is removed; the doctor plays uncut (the 0.9 s pause after «أنت كشاب» carries the hook title)."""
SRC = "/mnt/project-files/بوتوكس الرجال.mp4"
FPS = 30; XF = 6
KEEP_F = [(50, 908)]
KEEP = [(a / FPS, b / FPS) for a, b in KEEP_F]
STARTS = []; _acc = 0
for k, (a, b) in enumerate(KEEP_F):
    STARTS.append(_acc); _acc += (b - a) - XF
DOC_FRAMES = _acc + XF
DOC_LEN = DOC_FRAMES / FPS
CUTS = [round((STARTS[k] + XF / 2) / FPS, 4) for k in range(1, len(KEEP_F))]
def o(r):
    f = r * FPS
    for k in range(len(KEEP_F) - 1, -1, -1):
        a, b = KEEP_F[k]
        if f >= a: return round((STARTS[k] + min(f, b) - a) / FPS, 4)
    return 0.0
