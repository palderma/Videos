#!/usr/bin/env python3
"""Colour grade for «أسباب فشل علاج الكلف»: neutral warm-white wall (was grey + slight cyan), lifted exposure,
gentle S-curve, scrubs nudged toward Palderma wine (no saturation push), desk orange calmed, skin untouched in hue.
grade(rgb uint8) -> rgb uint8"""
import numpy as np, cv2
H_, W_ = 1920, 1080
_yy = np.mgrid[0:H_, 0:W_][0].astype(np.float32)
DESK = np.clip((_yy - 1560) / 120, 0, 1)            # desk lives below y≈1560 (hands end ~1600)
def grade(rgb):
    x = rgb.astype(np.float32) / 255
    # white balance: wall (206,211,210) -> neutral
    x *= np.array([1.030, 1.0, 1.003], np.float32)
    # exposure lift that mostly moves the wall/highlights: wall ~0.83 -> ~0.90, mids +3 %
    x = np.clip(x, 0, 1)
    x = x + 0.11 * x ** 2 * (1 - x) * 2.2
    # soft S-curve for depth
    x = x + 0.035 * np.sin((x - 0.5) * 2 * np.pi) * (x > 0.04) * (x < 0.96)
    x = np.clip(x, 0, 1)
    hsv = cv2.cvtColor(x, cv2.COLOR_RGB2HSV)
    Hh, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    # scrubs: magenta-violet (300-350) -> toward wine 342, same saturation, a touch deeper
    d = ((Hh - 330 + 180) % 360) - 180
    m = np.clip((S - 0.25) / 0.15, 0, 1) * np.clip(1 - np.abs(d) / 32, 0, 1) * np.clip((0.75 - V) / 0.2, 0, 1)
    m = cv2.GaussianBlur(m, (0, 0), 2)
    Hh[:] = (Hh + (342 - (Hh % 360)) * 0.45 * m * (np.abs(342 - Hh) < 60)) % 360
    S[:] = np.clip(S * (1 + 0.04 * m), 0, 1); V[:] = V * (1 - 0.04 * m)
    # desk: calm the orange wood a bit (spatial mask keeps the hands/skin out)
    dk = DESK * np.clip(1 - np.abs(((Hh - 33 + 180) % 360) - 180) / 25, 0, 1)
    S[:] = S * (1 - 0.15 * dk)
    out = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
if __name__ == "__main__":
    import sys
    from PIL import Image
    a = np.array(Image.open(sys.argv[1]).convert("RGB")); b = grade(a)
    for p in [(100, 200), (900, 300), (540, 1100), (540, 1700), (510, 700)]: print(p, a[p[1], p[0]], b[p[1], p[0]])
    Image.fromarray(np.hstack([a, b])[::2, ::2]).save(sys.argv[2], quality=90)
