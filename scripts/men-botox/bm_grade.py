#!/usr/bin/env python3
"""Colour grade for «ضرورة واقي الشمس بالشتاء» (sunny window behind the doctor, like «تجمع سوائل»):
warm white balance against the window's blue, highlight roll-off (sky/blinds recover detail), midtone lift so the
doctor is brighter than before, gentle S-curve, scrubs nudged toward Palderma wine. grade(rgb uint8) -> rgb uint8"""
import numpy as np, cv2
def grade(rgb):
    x = rgb.astype(np.float32) / 255
    x *= np.array([1.035, 1.0, 0.955], np.float32)                       # WB: warmer
    x = np.clip(x, 0, 1)
    L = x.max(-1, keepdims=True)
    k = 0.80                                                              # highlight roll-off above the knee
    hi = np.where(L > k, k + (1 - k) * np.tanh((L - k) / (1 - k) * 1.0) / np.tanh(1.0) * 0.93, L)
    x = x * (hi / np.maximum(L, 1e-4))
    x = x + 0.10 * x * (1 - x) ** 1.5                                     # midtone/shadow lift (doctor)
    x = x + 0.03 * np.sin((x - 0.5) * 2 * np.pi) * (x > 0.04) * (x < 0.96)  # soft S-curve
    x = np.clip(x, 0, 1)
    hsv = cv2.cvtColor(x.astype(np.float32), cv2.COLOR_RGB2HSV)
    Hh, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    d = ((Hh - 335 + 180) % 360) - 180                                    # scrubs (magenta-wine) -> 342, a touch richer
    m = np.clip((S - 0.25) / 0.15, 0, 1) * np.clip(1 - np.abs(d) / 30, 0, 1) * np.clip((0.8 - V) / 0.2, 0, 1)
    m = cv2.GaussianBlur(m, (0, 0), 2)
    Hh[:] = (Hh + ((342 - Hh + 180) % 360 - 180) * 0.4 * m) % 360
    S[:] = np.clip(S * (1 + 0.06 * m), 0, 1)
    out = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    return (np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8)
if __name__ == "__main__":
    import sys
    from PIL import Image
    a = np.array(Image.open(sys.argv[1]).convert("RGB")); b = grade(a)
    Image.fromarray(np.hstack([a, b])[::2, ::2]).save(sys.argv[2], quality=90)
