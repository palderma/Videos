# photo card: crop the bumpy upper-arm area, rounded corners, pink border, small credit line
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
W, H, R, B = 720, 780, 40, 7
im = Image.open("/home/user/gb/kp/a.jpg").convert("RGB")
x0, y0 = 60, 120; cw = 1180; ch = int(cw * H / W)
im = im.crop((x0, y0, x0 + cw, y0 + ch)).resize((W, H), Image.LANCZOS)
a = np.array(im, np.float32)
# gentle grade: a touch warmer/cleaner, small contrast so the bumps read on a phone
a = np.clip((a - 128) * 1.08 + 128 + np.array([4, 0, 2]), 0, 255)
# credit strip gradient at the bottom
g = np.linspace(0, 1, 90)[:, None, None] ** 1.6
a[-90:] = a[-90:] * (1 - 0.55 * g)
img = Image.fromarray(a.astype(np.uint8)).convert("RGBA")
d = ImageDraw.Draw(img)
f = ImageFont.truetype("/home/user/Videos/brand/fonts/thmanyahsans-Regular.otf", 22)
d.text((W - 24, H - 22), "Photo: Irja / Wikimedia Commons, CC BY-SA 2.0", font=f, fill=(255, 255, 255, 215), anchor="rs")
# rounded mask + pink border
ss = 4
m = Image.new("L", (W * ss, H * ss), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, W * ss - 1, H * ss - 1), R * ss, fill=255)
m = m.resize((W, H), Image.LANCZOS)
bd = Image.new("L", (W * ss, H * ss), 0); ImageDraw.Draw(bd).rounded_rectangle((0, 0, W * ss - 1, H * ss - 1), R * ss, outline=255, width=B * ss)
bd = bd.resize((W, H), Image.LANCZOS)
pink = Image.new("RGBA", (W, H), (243, 165, 189, 255))
img = Image.composite(pink, img, bd)
img.putalpha(m)
img.save("/home/user/gb/kp/card.png")
print(img.size)
