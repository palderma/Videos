"""v5 clock: explainer intro before the v4 timeline + reading holds inserted at static moments (v4 source times)."""
INTRO = 5.0
INS = [(1.75, 0.6), (3.5, 0.9), (5.2, 1.1), (6.85, 0.9), (8.45, 1.1), (10.1, 0.9), (12.6, 1.3), (14.55, 0.9), (16.1, 0.9)]
def g(t):
    return t + INTRO + sum(d for p, d in INS if t > p)
