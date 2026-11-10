#!/usr/bin/env python3
"""Export the gb.py scene as an After Effects ExtendScript that BUILDS the .aep (native layers + keyframes).
Faces -> precomps with live text layers; flaps / strips -> 3D precomp layers + rectangle masks parented to 3D nulls;
camera, motion blur, shading as a Fill effect driven by an expression on the layer's own rotation.
Usage: python3 gb_jsx.py <package_dir>"""
import os, sys, json, shutil
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import gb, kf
from kf import K

def js(v): return json.dumps(v, ensure_ascii=False)
def col(c): return [round(x / 255, 4) for x in c]
def r(v, n=3):
    if isinstance(v, (list, tuple)): return [round(float(x), n) for x in v]
    return round(float(v), n)

def keys(p, conv=lambda v: v):
    """-> [[t, v, in, out]] sorted, duplicates removed; static -> [[0, v]]"""
    if not (isinstance(p, list) and p and isinstance(p[0], K)): return [[0, conv(p)]]
    ks = sorted(p, key=lambda k: k.t); out = []
    for kk in ks:
        if out and abs(out[-1][0] - kk.t) < 1e-3: out.pop()
        out.append([round(kk.t, 4), conv(kk.v), max(0.1, min(100, kk.i)), max(0.1, min(100, kk.o)), 1 if kk.lin else 0])
    if len(out) == 1: return [[0, out[0][1]]]
    return out

HEAD = r'''// جلد الأوزة: 3 أفكار غلط - Palderma (Kinetic Typography / Split-Flap)
// هذا السكربت يبني مشروع After Effects كامل (AEP) بطبقات وكيفريمات قابلة للتعديل.
// الاستعمال: 1) ثبّت خطوط ثمانية من مجلد fonts  2) افتح After Effects  3) File > Scripts > Run Script File... واختار هالملف
// 4) بعد ما يخلص: File > Save As واحفظه .aep جنب هالملف.  لازم يضل السكربت جنب مجلدات footage و audio.
// تعديل الكلام: افتح الكومب من مجلد «وجوه البلاطات» وعدّل طبقة النص؛ كل الشرائح والقلبات بتتحدث لحالها (ما في تكسير للحروف).
// إذا شفت القلبات طالعة لورا بدل ما تنزل لقدام، غيّر FLIP لـ -1 وشغّل السكربت من جديد.
#target aftereffects
(function () {
var FLIP = 1;
var root = new File($.fileName).parent;
app.beginUndoGroup("Palderma - جلد الأوزة");
if (!app.project) app.newProject();
var proj = app.project;
var ERRS = [];
var top = proj.items.addFolder("جلد الأوزة - 3 أفكار غلط - Palderma");
var fFoot = proj.items.addFolder("Footage"); fFoot.parentFolder = top;
var fFace = proj.items.addFolder("وجوه البلاطات (عدّل النص هون)"); fFace.parentFolder = top;
var cache = {};
function imp(p) { if (cache[p]) return cache[p]; var f = new File(root.fsName + "/" + p);
  if (!f.exists) { ERRS.push("الملف مش موجود: " + p); return null; }
  var it = proj.importFile(new ImportOptions(f)); it.parentFolder = fFoot; cache[p] = it; return it; }
function TR(L, m) { return L.property("ADBE Transform Group").property(m); }
function setK(prop, ks, mul, spatial) {
  function M(v) { if (mul == 1) return v; if (v instanceof Array) { var o = []; for (var j = 0; j < v.length; j++) o.push(v[j] * mul); return o; } return v * mul; }
  if (ks.length == 1 && ks[0].length == 2) { prop.setValue(M(ks[0][1])); return; }
  for (var i = 0; i < ks.length; i++) prop.setValueAtTime(ks[i][0], M(ks[i][1]));
  for (var i = 0; i < ks.length; i++) {
    var k = i + 1;
    if (ks[i][4] == 1) { try { prop.setInterpolationTypeAtKey(k, KeyframeInterpolationType.LINEAR, KeyframeInterpolationType.LINEAR); } catch (e) {} }
    else {
      var dims = (prop.propertyValueType == PropertyValueType.TwoD || prop.propertyValueType == PropertyValueType.TwoD_SPATIAL) ? 2 :
                 ((prop.propertyValueType == PropertyValueType.ThreeD || prop.propertyValueType == PropertyValueType.ThreeD_SPATIAL) ? 3 : 1);
      if (spatial) dims = 1;
      var ei = [], eo = [];
      for (var d = 0; d < dims; d++) { ei.push(new KeyframeEase(0, ks[i][2])); eo.push(new KeyframeEase(0, ks[i][3])); }
      try { prop.setTemporalEaseAtKey(k, ei, eo); } catch (e) {}
    }
    if (spatial) { try { prop.setSpatialAutoBezierAtKey(k, false); prop.setSpatialContinuousAtKey(k, false);
      var z = (prop.value.length == 3) ? [0, 0, 0] : [0, 0]; prop.setSpatialTangentsAtKey(k, z, z); } catch (e) {} }
  }
}
function rectShape(comp, name, w, h, rad, pos, fillCol, fillOp, strokeCol, strokeW) {
  var L = comp.layers.addShape(); L.name = name;
  L.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group");
  var V = function () { return L.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group"); };
  V().addProperty("ADBE Vector Shape - Rect");
  if (strokeCol) V().addProperty("ADBE Vector Graphic - Stroke");
  if (fillCol) V().addProperty("ADBE Vector Graphic - Fill");
  var S = V().property(1);
  S.property("ADBE Vector Rect Size").setValue([w, h]); S.property("ADBE Vector Rect Roundness").setValue(rad);
  if (strokeCol) { var ST = V().property("ADBE Vector Graphic - Stroke"); ST.property("ADBE Vector Stroke Color").setValue(strokeCol); ST.property("ADBE Vector Stroke Width").setValue(strokeW); }
  if (fillCol) { var FL = V().property("ADBE Vector Graphic - Fill"); FL.property("ADBE Vector Fill Color").setValue(fillCol); FL.property("ADBE Vector Fill Opacity").setValue(fillOp); }
  TR(L, "ADBE Anchor Point").setValue([0, 0]); TR(L, "ADBE Position").setValue(pos);
  return L;
}
function rectMask(L, x0, y0, x1, y1) {
  var m = L.property("ADBE Mask Parade").addProperty("ADBE Mask Atom");
  var s = new Shape(); s.vertices = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]; s.closed = true;
  m.property("ADBE Mask Shape").setValue(s); return m;
}
function faceComp(name, w, h, dur, card, txt) {
  var C = proj.items.addComp(name, w, h, 1, dur, 30); C.parentFolder = fFace;
  if (card) {
    rectShape(C, "البطاقة", w - 2, h - 2, card.r, [w / 2, h / 2], card.fill, 100, card.stroke, 2);
    var hl = rectShape(C, "إضاءة النص العلوي", w - 2, h - 2, card.r, [w / 2, h / 2], [1, 1, 1], 6, null, 0);
    rectMask(hl, 0, 0, w, h / 2);
    if (card.hinge) rectShape(C, "خط المفصل", w, 4, 0, [w / 2, h / 2], [0, 0, 0], 55, null, 0);
  }
  if (txt) faceText(C, txt, w / 2);
  return C;
}
function faceText(C, txt, x) {
  {
    var L = C.layers.addText(txt.s); L.name = "النص: " + txt.s;
    var p = L.property("ADBE Text Properties").property("ADBE Text Document"); var td = p.value;
    try { td.resetCharStyle(); td.resetParagraphStyle(); } catch (e) {}
    td.font = txt.font; td.fontSize = txt.size; td.applyFill = true; td.fillColor = txt.col; td.applyStroke = false; td.tracking = 0;
    td.justification = ParagraphJustification.CENTER_JUSTIFY;
    try { td.paragraphDirection = ParagraphDirection.DIRECTION_RIGHT_TO_LEFT; } catch (e) {}
    p.setValue(td);
    TR(L, "ADBE Anchor Point").expression = "var r = sourceRectAtTime(time, false); [r.left + r.width / 2, 0];";
    TR(L, "ADBE Position").setValue([x, txt.base]);
  }
  return L;
}
function fx(L, mn) { return L.property("ADBE Effect Parade").addProperty(mn); }
function effP(E, matchName, idx) { try { var p = E.property(matchName); if (p) return p; } catch (e) {} return E.property(idx); }
'''

def main(pkg):
    gb.build()
    os.makedirs(pkg, exist_ok=True)
    for d in ("footage", "audio", "fonts"): os.makedirs(os.path.join(pkg, d), exist_ok=True)
    gb.background()
    shutil.copy(os.path.join(gb.WORK, "assets", "خلفية.png"), os.path.join(pkg, "footage", "خلفية.png"))
    out = [HEAD]; w = out.append
    w("var MAIN = proj.items.addComp(%s, 1080, 1920, 1, %s, 30); MAIN.parentFolder = top; MAIN.bgColor = %s; MAIN.motionBlur = true;\n" % (
        js("جلد الأوزة - 3 أفكار غلط (9x16)"), gb.VLEN, js(col(gb.WINE))))
    MK = getattr(gb, "MARKERS", None) or [(0, "المشهد 1: العنوان"), (2.22, "المشهد 2: مستحيل تروح ← هاي شائعة"), (5.5, "المشهد 3: خطيرة ← غالبًا عادي"),
                 (8.5, "المشهد 4: ما إلها حل ← إلها خيارات بعد الفحص"), (12.05, "المشهد 5: الدعوة: ابعتوه لحدا بيخبي ذراعه بالأكمام"), (14.75, "الشعار الرسمي")]
    for t, m in MK:
        w("try { MAIN.markerProperty.setValueAtTime(%s, new MarkerValue(%s)); } catch (e) {}\n" % (t, js(m)))
    # faces
    fvar = {}
    used = {p.face for p in gb.PIECES}
    for i, (nm, f) in enumerate(gb.FACES.items()):
        if nm not in used: continue
        v = "F%d" % i; fvar[nm] = v
        if hasattr(f, "path_png"):
            rel = "footage/" + os.path.basename(f.path_png)
            shutil.copy(f.path_png, os.path.join(pkg, rel))
            w("var %s = imp(%s);\n" % (v, js(rel)))
            continue
        card = "null" if f.fill is None else js({"r": f.radius, "fill": col(f.fill), "stroke": col(f.stroke) if f.stroke else None, "hinge": bool(f.hinge)})
        txt = "null" if not f.txt else js({"s": f.txt, "font": kf.FONT_PS[f.weight], "size": f.size, "col": col(f.color), "base": round(f.base, 2)})
        w("var %s = faceComp(%s, %d, %d, %s, %s, %s);\n" % (v, js("وجه - " + nm), f.w, f.h, gb.VLEN, card, txt))
        for it in getattr(f, "items", []):
            if it["kind"] == "rect":
                w("rectShape(%s, 'خلفية داخلية', %s, %s, %s, %s, %s, 100, null, 0);\n" % (v, it["w"], it["h"], it["r"], js([it["x"], it["y"]]), js(col(it["fill"]))))
            else:
                w("faceText(%s, %s, %s);\n" % (v, js({"s": it["s"], "font": kf.FONT_PS[it.get("weight", "Bold")], "size": it["size"], "col": col(it["col"]), "base": round(it["base"], 2)}), round(it["x"], 2)))
    # background
    w("try { var BG = MAIN.layers.add(imp('footage/خلفية.png')); BG.name = 'الخلفية العنابية'; BG.locked = true; } catch (e) { ERRS.push('bg: ' + e); }\n")
    # nulls
    nvar = {}
    for i, n in enumerate(gb.NULLS):
        v = "N%d" % i; nvar[id(n)] = v
        w("var %s = MAIN.layers.addNull(); %s.name = %s; %s.threeDLayer = true; TR(%s,'ADBE Anchor Point').setValue([0,0,0]);\n" % (v, v, js(n.name), v, v))
        w("setK(TR(%s,'ADBE Position'), %s, 1, true);\n" % (v, js(keys(n.pos, lambda x: r(x, 2)))))
        w("setK(TR(%s,'ADBE Scale'), %s, 1, false);\n" % (v, js(keys(n.scale, lambda x: [r(x), r(x), r(x)]))))
        w("setK(TR(%s,'ADBE Opacity'), %s, 1, false);\n" % (v, js(keys(n.op, r))))
    # layers bottom -> top
    for L in gb.LAYERS:
        w("try {\n")
        if isinstance(L, gb.Piece):
            f = gb.FACES[L.face]
            w("var L = MAIN.layers.add(%s); L.name = %s; L.threeDLayer = true; L.motionBlur = true;\n" % (fvar[L.face], js(L.name)))
            x0, y0, x1, y1 = L.crop
            if not (x0 <= 0 and y0 <= 0 and x1 >= f.w and y1 >= f.h):
                w("rectMask(L, %s, %s, %s, %s);\n" % (r(x0, 2), r(y0, 2), r(x1, 2), r(y1, 2)))
            if L.parent is not None: w("L.parent = %s;\n" % nvar[id(L.parent)])
            outp = L.outp if L.outp is not None else gb.VLEN
            w("try { L.inPoint = %s; L.outPoint = %s; } catch (e) {}\n" % (r(max(0, L.inp)), r(min(outp, gb.VLEN))))
            w("TR(L,'ADBE Anchor Point').setValue(%s);\n" % js([r(L.anchor[0], 2), r(L.anchor[1], 2), 0]))
            w("setK(TR(L,'ADBE Position'), %s, 1, true);\n" % js(keys(L.pos, lambda x: r(x, 2))))
            w("setK(TR(L,'ADBE Scale'), %s, 1, false);\n" % js(keys(L.scale, lambda x: [r(x), r(x), r(x)])))
            if kf.animated(L.rx) or L.rx: w("setK(TR(L,'ADBE Rotate X'), %s, FLIP, false);\n" % js(keys(L.rx, r)))
            if kf.animated(L.ry) or L.ry: w("setK(TR(L,'ADBE Rotate Y'), %s, 1, false);\n" % js(keys(L.ry, r)))
            if kf.animated(L.rz) or L.rz: w("setK(TR(L,'ADBE Rotate Z'), %s, 1, false);\n" % js(keys(L.rz, r)))
            w("setK(TR(L,'ADBE Opacity'), %s, 1, false);\n" % js(keys(L.op, r)))
            if L.parent is not None:
                w("TR(L,'ADBE Opacity').expression = 'value * (hasParent ? parent.transform.opacity : 100) / 100';\n")
            if L.shade:
                w("var SH = fx(L, 'ADBE Fill'); SH.name = 'ظل القلبة'; try { effP(SH, 'ADBE Fill-0002', 3).setValue([0.08, 0, 0.03, 1]); } catch (e) {}\n"
                  "try { effP(SH, 'ADBE Fill-0005', 7).expression = 'var a = Math.abs(Math.sin(degreesToRadians(transform.xRotation))) + Math.abs(Math.sin(degreesToRadians(transform.yRotation))); Math.min(1, a) * 50'; } catch (e) {}\n")
            if kf.animated(L.blur) or L.blur:
                w("var GB = fx(L, 'ADBE Gaussian Blur 2'); try { GB.property('ADBE Gaussian Blur 2-0003').setValue(1); } catch (e) {}\nsetK(GB.property(1), %s, 1, false);\n" % js(keys(L.blur, r)))
        else:
            S = L
            w("var L = MAIN.layers.addShape(); L.name = %s;\n" % js(S.name))
            w("L.property('ADBE Root Vectors Group').addProperty('ADBE Vector Group');\n"
              "var V = function () { return L.property('ADBE Root Vectors Group').property(1).property('ADBE Vectors Group'); };\n")
            if S.kind == "disc":
                w("V().addProperty('ADBE Vector Shape - Ellipse'); V().addProperty('ADBE Vector Graphic - Fill');\n"
                  "var SZ = V().property(1).property('ADBE Vector Ellipse Size');\n")
            else:
                w("V().addProperty('ADBE Vector Shape - Rect'); V().addProperty('ADBE Vector Graphic - Fill');\n"
                  "var SZ = V().property(1).property('ADBE Vector Rect Size'); V().property(1).property('ADBE Vector Rect Roundness').setValue(100);\n")
            w("V().property('ADBE Vector Graphic - Fill').property('ADBE Vector Fill Color').setValue(%s);\n" % js(col(S.color)))
            w("setK(SZ, %s, 1, false);\n" % js(keys(S.size, lambda x: r(x, 2))))
            w("TR(L,'ADBE Anchor Point').setValue([0,0]);\nsetK(TR(L,'ADBE Position'), %s, 1, true);\n" % js(keys(S.pos, lambda x: r(x, 2))))
            w("setK(TR(L,'ADBE Opacity'), %s, 1, false);\n" % js(keys(S.op, r)))
            outp = S.outp if S.outp is not None else gb.VLEN
            w("try { L.inPoint = %s; L.outPoint = %s; } catch (e) {}\n" % (r(max(0, S.inp)), r(min(outp, gb.VLEN))))
        w("} catch (err) { ERRS.push(%s + ': ' + err.toString() + ' (line ' + err.line + ')'); }\n" % js(L.name))
    ex = getattr(gb, "JSX_EXTRA", None)
    if ex: w(ex(pkg, js, r))
    # camera + audio
    w('''try { var CAM = MAIN.layers.addCamera("الكاميرا", [540, 960]);
  CAM.property("ADBE Camera Options Group").property("ADBE Camera Zoom").setValue(%s);
  TR(CAM, "ADBE Anchor Point").setValue([540, 960, 0]); TR(CAM, "ADBE Position").setValue([540, 960, -%s]); } catch (e) { ERRS.push("camera: " + e); }
''' % (gb.CAM, gb.CAM))
    for nm, rel in (("الصوت - ميكس نهائي", "audio/mix.wav"), ("الصوت - موسيقى فقط (مطفي)", "audio/music.wav"), ("الصوت - مؤثرات القلب فقط (مطفي)", "audio/sfx.wav")):
        off = "مطفي" in nm
        w("try { var A = MAIN.layers.add(imp(%s)); A.name = %s; A.moveToEnd(); %s } catch (e) { ERRS.push('audio: ' + e); }\n" % (
            js(rel), js(nm), "A.audioEnabled = false;" if off else ""))
    w('''app.endUndoGroup();
MAIN.openInViewer();
if (ERRS.length) alert("انبنى المشروع، بس في طبقات ما زبطت (ابعت صورة عن هالرسالة):\\n" + ERRS.slice(0, 15).join("\\n"));
else alert("تمام! انبنى مشروع «جلد الأوزة» بكل الطبقات والكيفريمات. احفظه: File > Save As (.aep)");
})();
''')
    open(os.path.join(pkg, "build_project.jsx"), "w", encoding="utf-8-sig").write("".join(out))
    for fn in os.listdir(gb.BRAND + "/fonts"): shutil.copy(os.path.join(gb.BRAND, "fonts", fn), os.path.join(pkg, "fonts", fn))
    for a in ("mix.wav", "music.wav", "sfx.wav"): shutil.copy(os.path.join(gb.WORK, a), os.path.join(pkg, "audio", a))
    print("layers:", len(gb.LAYERS), "nulls:", len(gb.NULLS), "faces:", len(fvar))

if __name__ == "__main__":
    main(sys.argv[1])
