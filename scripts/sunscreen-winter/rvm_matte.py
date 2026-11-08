#!/usr/bin/env python3
"""RVM matte: rvm_matte.py in.mp4 out_alpha.mkv  (gray ffv1, same size/fps)"""
import sys, subprocess, numpy as np, onnxruntime as ort
src, dst = sys.argv[1], sys.argv[2]
ds = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25
W, H = 1080, 1920
so = ort.SessionOptions(); so.intra_op_num_threads = 4
sess = ort.InferenceSession("/home/user/rvm.onnx", so, providers=["CPUExecutionProvider"])
rd = subprocess.Popen(["ffmpeg", "-v", "error", "-i", src, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], stdout=subprocess.PIPE)
wr = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{W}x{H}", "-r", "30", "-i", "-", "-c:v", "ffv1", dst], stdin=subprocess.PIPE)
rec = [np.zeros((1, 1, 1, 1), np.float32)] * 4
dr = np.array([ds], np.float32); n = 0
while True:
    b = rd.stdout.read(W * H * 3)
    if len(b) < W * H * 3: break
    x = np.frombuffer(b, np.uint8).reshape(H, W, 3).transpose(2, 0, 1)[None].astype(np.float32) / 255
    fgr, pha, *rec = sess.run(None, {"src": x, "r1i": rec[0], "r2i": rec[1], "r3i": rec[2], "r4i": rec[3], "downsample_ratio": dr})
    wr.stdin.write((np.clip(pha[0, 0], 0, 1) * 255 + 0.5).astype(np.uint8).tobytes()); n += 1
    if n % 100 == 0: print(n, flush=True)
wr.stdin.close(); wr.wait(); print("done", n)
