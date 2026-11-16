#!/usr/bin/env python3
"""After Effects package for «الجليد المنصهر»:
 - footage/ice_color.mp4 + footage/ice_matte.mp4 (frost colour & coverage passes from ice_fx)
 - build_project.jsx (kf export): content precomp with native text/shape/image layers + keyframes,
   frosted copy (blur) and frost colour both matted by ice_matte (luma), title precomp on the ice.
python3 ae.py passes | python3 ae.py pack <dir>"""
import os, sys, shutil, subprocess
sys.path.insert(0, "/home/user/ice")
import numpy as np
import kf
from kf import K, Comp, precomp, footage, audio
import ice_fx as IF
import scene as S

WK = "/home/user/ice/work"

def ice_pass(t, EVS):
    kind, st = IF.state(EVS, t)
    if kind == "none":
        return np.zeros((IF.H, IF.W, 3), np.float32), np.zeros((IF.H, IF.W), np.float32)
    if kind == "full":
        cov = np.ones((IF.H, IF.W), np.float32); th = cov; front = None
    else:
        e, thr, cov, th = st; front = (e, thr)
    fa = (0.90 + 0.08 * IF.F["frost"]) * (0.30 + 0.70 * th)
    I = IF.ice_color(t)
    nxt = next((e for e in EVS if e.kind == "melt" and e.crack_at is not None and e.crack_at <= t <= e.t1), None)
    if nxt is not None:
        cm = IF.crack_mask(nxt, t)
        if cm is not None:
            I = I * (1 - 0.55 * cm[..., None]) + IF.CRACK_C * 0.55 * cm[..., None]
            fa = np.maximum(fa, cm * 0.9)
    if front is not None and front[0].kind == "freeze":
        e, thr = front
        I += (np.exp(-((e.N - thr) / 0.025) ** 2) * (0.5 + 0.8 * IF.F["feather"]) * 90)[..., None]
    g = S.glint(t)
    if g is not None:
        s = IF.XX * 0.55 + IF.YY * 0.85
        I += ((np.exp(-((s - g) / 70) ** 2) * 0.55 + np.exp(-((s - g + 160) / 22) ** 2) * 0.35) * 55)[..., None]
    I += (IF.sparkles(t, 1.0) * 200)[..., None]
    return np.clip(I, 0, 255), np.clip(cov * fa, 0, 1)

def passes():
    EVS = S.evs(); n = int(round(S.TOTAL * 30))
    def enc(path):
        return subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1080x1920", "-r", "30", "-i", "-",
                                 "-c:v", "libx264", "-preset", "slow", "-crf", "21", "-pix_fmt", "yuv420p", "-movflags", "+faststart", path], stdin=subprocess.PIPE)
    pc, pm = enc(WK + "/ice_color.mp4"), enc(WK + "/ice_matte.mp4")
    for i in range(n):
        c, m = ice_pass(i / 30, EVS)
        pc.stdin.write(c.astype(np.uint8).tobytes())
        pm.stdin.write(np.repeat((m * 255)[..., None], 3, 2).astype(np.uint8).tobytes())
    pc.stdin.close(); pm.stdin.close(); pc.wait(); pm.wait()

def pack(d):
    os.makedirs(d + "/footage", exist_ok=True); os.makedirs(d + "/audio", exist_ok=True); os.makedirs(d + "/fonts", exist_ok=True)
    C, T = S.build()
    fm = {}
    def reg(p, sub):
        rel = sub + "/" + os.path.basename(p)
        if p not in fm:
            shutil.copy(p, os.path.join(d, rel)); fm[p] = rel
    for comp in (C, T):
        for L in comp.layers:
            if L.kind in ("image", "footage"): reg(L.kw["path"], "footage")
    ic, im = WK + "/ice_color.mp4", WK + "/ice_matte.mp4"
    reg(ic, "footage"); reg(im, "footage")
    au = WK + "/audio.wav"; reg(au, "audio")
    for f in os.listdir(kf.FONT_DIR): shutil.copy(os.path.join(kf.FONT_DIR, f), d + "/fonts/")
    M = Comp("الجليد المنصهر - ريلز 9x16 (MAIN)", 1080, 1920, S.TOTAL, 30, bg=S.WINE)
    M.add(precomp("المحتوى (عنابي)", C, comment="كل النصوص والأيقونات قابلة للتعديل جوّا هالكومب"))
    M.add(precomp("المحتوى تحت الجليد (مغبّش)", C, blur=60, matte=footage("مات الجليد", im), matte_mode="luma"))
    M.add(footage("لون الجليد", ic, matte=footage("مات الجليد", im), matte_mode="luma"))
    M.add(precomp("العنوان على الجليد", T, matte=footage("مات الجليد", im), matte_mode="luma"))
    M.add(audio("الصوت (موسيقى + مؤثرات)", au))
    M.markers = C.markers
    kf.export_jsx(M, d + "/build_project.jsx", "الجليد المنصهر - ليش الشتا موسم التقشير", fm)
    open(d + "/اقرأني.txt", "w", encoding="utf-8").write(
        "الجليد المنصهر - ليش الشتا موسم التقشير؟ (بالديرما)\n\n"
        "1) ثبّت خطوط ثمانية من مجلد fonts.\n"
        "2) افتح After Effects ثم File > Scripts > Run Script File... واختار build_project.jsx (خليه جنب مجلدات footage و audio).\n"
        "3) بعد ما يخلص احفظ المشروع .aep.\n\n"
        "التركيب: كومب «المحتوى (عنابي)» فيه كل النصوص (كل كلمة طبقة لحالها، الكلمات الوردية منفصلة) والأيقونات والكيفريمات.\n"
        "الجليد = طبقة «لون الجليد» + نسخة مغبّشة من المحتوى، والاثنين ماخدين شكل الذوبان والتجمّد من «مات الجليد» (Luma Matte).\n"
        "العنوان الأول موجود في كومب «العنوان على الجليد» وبيذوب مع الجليد.\n"
        "الماركرات على التايملاين بتبيّن وقت كل تشقق وذوبان وتجمّد.\n"
        "ملاحظة: انكسار الضوء على حافة الذوبان وقطرات المي موجودين بالفيديو النهائي MP4 بس، مش بمشروع الأفترافكت.\n")

if __name__ == "__main__":
    if sys.argv[1] == "passes": passes()
    else: pack(sys.argv[2])
