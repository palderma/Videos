"""Lucide-style icons (ISC licence; paths from lucide.dev or drawn in the same 24px stroke style) -> PNG."""
import os, re, cairosvg
OUT = os.environ.get("ICE_ICONS", "/home/user/ice/work/icons")
LUC = "/mnt/project-files/style-guide/assets/icons/lucide/"

P = {
    # lucide cloud-sun
    "cloud-sun": ['<path d="M12 2v2"/>', '<path d="m4.93 4.93 1.41 1.41"/>', '<path d="M20 12h2"/>',
                  '<path d="m19.07 4.93-1.41 1.41"/>', '<path d="M15.947 12.65a4 4 0 0 0-5.925-4.128"/>',
                  '<path d="M13 22H7a5 5 0 1 1 4.9-6H13a3 3 0 0 1 0 6Z"/>'],
    # lucide shield (outline) and its check
    "shield": ['<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/>'],
    "check": ['<path d="m9 12 2 2 4-4"/>'],
    "scan-face": ['<path d="M3 7V5a2 2 0 0 1 2-2h2"/>', '<path d="M17 3h2a2 2 0 0 1 2 2v2"/>', '<path d="M21 17v2a2 2 0 0 1-2 2h-2"/>',
                  '<path d="M7 21H5a2 2 0 0 1-2-2v-2"/>', '<path d="M8 14s1.5 2 4 2 4-2 4-2"/>', '<path d="M9 9h.01"/>', '<path d="M15 9h.01"/>'],
    # sunscreen tube (drawn in lucide style): body, cap, small sun on the label
    "tube": ['<path d="M7 9.5 6.2 21a1 1 0 0 0 1 1h9.6a1 1 0 0 0 1-1L17 9.5Z"/>', '<path d="M8.5 9.5V6.5a1 1 0 0 1 1-1h5a1 1 0 0 1 1 1v3"/>',
             '<path d="M10.5 5.5V3h3v2.5"/>', '<circle cx="12" cy="15.8" r="1.5"/>', '<path d="M12 11.9v.9"/>', '<path d="M12 18.8v.9"/>',
             '<path d="M8.1 15.8h.9"/>', '<path d="M15 15.8h.9"/>'],
    "bookmark": ['<path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/>'],
    "send": ['<path d="M14.536 21.686a.5.5 0 0 0 .937-.024l6.5-19a.496.496 0 0 0-.635-.635l-19 6.5a.5.5 0 0 0-.024.937l7.93 3.18a2 2 0 0 1 1.112 1.11z"/>',
             '<path d="m21.854 2.147-10.94 10.939"/>'],
}

def icon(name, color, px, sw=1.6, fill=None):
    os.makedirs(OUT, exist_ok=True)
    c = "#%02x%02x%02x" % tuple(color)
    f = "#%02x%02x%02x" % tuple(fill) if fill else "none"
    path = os.path.join(OUT, "%s-%s-%d%s.png" % (name, c[1:], px, "-fill" if fill else ""))
    if name not in P:
        txt = open(LUC + name + ".svg").read()
        P[name] = re.findall(r"<(?:path|circle|line|rect|polyline)\b[^>]*/>", txt)
    if not os.path.exists(path):
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 24 24" fill="%s" stroke="%s" '
               'stroke-width="%s" stroke-linecap="round" stroke-linejoin="round">%s</svg>') % (px, px, f, c, sw, "".join(P[name]))
        cairosvg.svg2png(bytestring=svg.encode(), write_to=path, output_width=px, output_height=px)
    return path
