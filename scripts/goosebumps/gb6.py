#!/usr/bin/env python3
"""«جلد الأوزة: 3 أفكار غلط» v6 (2026-11-10): v5 + the «غالبًا | عادي» pair centred on the frame
(v5 sat 40 px left with unequal tiles 410 | 490; now two equal 450 px tiles, gap on the centre line) + through-composed music (gb6_audio.py).
Usage: python3 gb6.py [--t=..] [--frames=a:b --out=DIR] [--sfx] [--jsx=PKGDIR] [--check]"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
os.environ["GB_WORK"] = os.environ.get("GB_WORK", "/home/user/gb/work6")
import gb4
gb4.PAIR_W = (450, 450)
gb4.PAIR_X = (540 + 10 + 225, 540 - 10 - 225)
import gb5
if __name__ == "__main__":
    import gb
    os.makedirs(gb.WORK, exist_ok=True)
    if "--check" in sys.argv:
        gb5.build5(); print("total", gb.VLEN); sys.exit()
    jsx = [a for a in sys.argv[1:] if a.startswith("--jsx=")]
    if jsx:
        sys.argv = [sys.argv[0]]
        import gb_jsx
        gb_jsx.main(jsx[0].split("=", 1)[1])
    else:
        gb.main()
