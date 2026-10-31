#!/usr/bin/env python3
"""v3 colour grade for the doctor shot: highlight roll-off + gentle dehaze on the bright window, scrubs pulled toward
Palderma wine, natural warm skin, a touch of contrast. grade(rgb uint8) -> rgb uint8"""
import numpy as np, cv2
def grade(rgb):
    f = rgb.astype(np.float32) / 255
    hsv = cv2.cvtColor(f, cv2.COLOR_RGB2HSV)            # H 0-360, S 0-1, V 0-1
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    # scrubs (magenta-purple) -> wine: hue toward ~340, slightly deeper
    m = np.clip((S - 0.18) / 0.15, 0, 1) * np.clip(1 - np.abs(((H - 312 + 180) % 360) - 180) / 40, 0, 1)
    m = cv2.GaussianBlur(m, (0, 0), 2)
    H[:] = (H + 14 * m) % 360; S[:] = S * (1 + 0.10 * m); V[:] = V * (1 - 0.10 * m)
    # bright hazy window: dehaze (lower + more contrast) where bright & low saturation
    hz = np.clip((V - 0.62) / 0.25, 0, 1) * np.clip(1 - S / 0.35, 0, 1)
    hz = cv2.GaussianBlur(hz, (0, 0), 6)
    V[:] = V - hz * (0.10 + 0.10 * (V - 0.62))
    S[:] = np.clip(S * (1 + 0.12 * hz), 0, 1)
    out = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    # highlight roll-off + soft S-curve
    x = np.clip(out, 0, 1)
    x = np.where(x > 0.8, 0.8 + (x - 0.8) * 0.7, x)
    x = x + 0.06 * np.sin((x - 0.5) * np.pi) * (x > 0.04)
    # warm a hair (skin), keep whites neutral
    x[..., 0] *= 1.015; x[..., 2] *= 0.985
    return (np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8)
