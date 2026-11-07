#!/usr/bin/env python3
"""Static assets for «أسباب فشل علاج الكلف» (pkg/footage): Lucide line icons, official logo, user's flash / messenger /
WhatsApp / pink outro files copied in (unchanged)."""
import os, io, shutil, cairosvg
from PIL import Image
O = "/home/user/klf/pkg/footage"; os.makedirs(O, exist_ok=True)
ICON_DIRS = ["/mnt/project-files/edits/scl_work/icons", "/mnt/project-files/edits/hl2_work/icons"]
def icon(name, size, col, out, stroke=2.0):
    p = next(os.path.join(d, name + ".svg") for d in ICON_DIRS if os.path.exists(os.path.join(d, name + ".svg")))
    svg = open(p).read().replace("currentColor", "#%02x%02x%02x" % col).replace('stroke-width="2"', f'stroke-width="{stroke}"')
    Image.open(io.BytesIO(cairosvg.svg2png(bytestring=svg.encode(), output_width=size, output_height=size))).convert("RGBA").save(f"{O}/{out}.png")
icon("droplet", 54, (0xF3, 0xA5, 0xBD), "icon_droplet_pink", 2.0)
icon("calendar-heart", 58, (255, 255, 255), "icon_calendar_heart_white", 2.0)
lg = Image.open("/home/user/Videos/brand/logo/arabic-english/png/burgundy.png").convert("RGBA")
lg = lg.crop(lg.getbbox()); lg.thumbnail((250, 250)); lg.save(f"{O}/logo_burgundy.png"); print("logo", lg.size)
for src, dst in [("/mnt/project-files/style-guide/assets/انتقال-فلاش.mov", "flash_transition.mov"),
                 ("/mnt/project-files/after-effects/assets/messenger-button-alpha.mov", "messenger_button.mov"),
                 ("/mnt/project-files/after-effects/assets/whatsapp-outro-alpha.mov", "whatsapp_pill.mov"),
                 ("/mnt/project-files/style-guide/assets/خاتمة-عمودي-9x16.mp4", "palderma_pink_outro.mp4")]:
    shutil.copy(src, f"{O}/{dst}")
print("ok")
