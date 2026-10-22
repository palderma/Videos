#!/usr/bin/env python3
"""Timeline for «البيبي فيس - جلسة الدراكولا» (raw: /mnt/project-files/Comp 1.mp4, doctor already keyed by the user
onto the clinic set, NOT mirrored). Word times from after-effects/baby-face-transcript.json (whisper large-v3).
First 1.2 s of silence trimmed; nothing else is cut. Output time = raw time - OFF.
Styles: n normal (word by word), k keyword (gradient, big), c normal + hand-drawn circle, - hidden (motion scene)."""
import json
RAW = "/mnt/project-files/Comp 1.mp4"
OFF = 1.2
RAW_END = 39.03 - OFF
_W = json.load(open("/mnt/project-files/after-effects/baby-face-transcript.json"))["words"]

GROUPS_SPEC = [  # (words, style)
    ("البيبي فيس", "k"), ("هو حلم كل صبية", "-"), ("للحصول عليه", "-"),
    ("طبعاً هاي المعلومة", "n"), ("كتير من الناس", "n"), ("ما بتعرف", "k"),
    ("إنه أنا كيف ممكن", "n"), ("أحصل على هاي النتيجة", "n"), ("بجلسة بسيطة جداً", "c"),
    ("لكن", "n"), ("أهم شي", "k"), ("الوقت اللي نختاره", "n"), ("من العام", "n"),
    ("جلسة الدراكولا", "-"), ("هي اللي ممكن تعطيني", "-"), ("جلسة البيبي فيس", "-"), ("اللي أنا بحتاجها", "-"),
    ("لكن بهمنا إنه تنعمل", "-"), ("بموسم الشتاء", "-"), ("أو في آخر الخريف", "-"),
    ("لأنه تحتاج", "-"), ("لفترة نقاهة", "-"), ("من خمسة أيام لأسبوع", "-"),
    ("وللاستفسار عن هذه الجلسة", "-"), ("ممكن مراسلتنا عبر رسائل الصفحة", "-"),
    ("وأهلاً وسهلاً فيكم", "-"), ("بمركز بالديرما", "-"),
]

def build():
    words, groups, i = [], [], 0
    for text, st in GROUPS_SPEC:
        g = dict(text=text, style=st, words=[])
        for w in text.split():
            src = _W[i]; assert src["word"] == w, (src["word"], w); i += 1
            words.append(dict(w=w, s=src["start"] - OFF, e=src["end"] - OFF, g=len(groups))); g["words"].append(len(words) - 1)
        g["s"] = words[g["words"][0]]["s"]; g["e"] = words[g["words"][-1]]["e"]; groups.append(g)
    assert i == len(_W)
    return words, groups

WORDS, GROUPS = build()
def gfind(text, n=0): return [g for g in GROUPS if g["text"] == text][n]
def wfind(w, n=0): return [x for x in WORDS if x["w"] == w][n]
def R(t): return round(t - OFF, 3)          # raw -> output
SPEECH_END = R(38.18)

T_PIP_IN, T_PIP_OUT = R(2.50), R(4.95)
#     hook doc, ch1 session, ch2 timing, ch3 recovery, doc
TB = [0.0, R(17.05), R(22.50), R(27.70), R(31.98)]
T_MSG = R(32.20)                            # page-messages overlay starts («وللاستفسار»)
T_MSG_OUT = R(37.00)                        # overlay fades out as he says «بمركز بالديرما» (user, 2026-10-22)
MSG_HOLD = (62, R(38.20))                   # overlay frame held (button clicked) until the speech ends
T_OUT = round(MSG_HOLD[1] + 0.1, 2)         # pink outro wipes in (user rule: never end on the Facebook page)
OUTRO_LEN = 8.0
DUR = round(T_OUT + OUTRO_LEN, 2)

if __name__ == "__main__":
    for g in GROUPS: print(f'{g["s"]:6.2f}-{g["e"]:6.2f} {g["style"]} {g["text"]}')
    print("TB", TB, "msg", T_MSG, "out", T_OUT, "dur", DUR)
