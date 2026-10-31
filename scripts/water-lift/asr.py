import sherpa_onnx, soundfile as sf, numpy as np, sys
D="/tmp/asr/sherpa-onnx-whisper-large-v3/"
r=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=D+"large-v3-encoder.int8.onnx",decoder=D+"large-v3-decoder.int8.onnx",tokens=D+"large-v3-tokens.txt",language="ar",task="transcribe",num_threads=4)
x,sr=sf.read("/home/user/sm/a16.wav",dtype="float32")
segs=[tuple(map(float,a.split(","))) for a in sys.argv[1:]]
for a,b in segs:
    s=r.create_stream(); s.accept_waveform(sr,x[int(a*sr):int(b*sr)]); r.decode_stream(s)
    print(f"{a:.2f}-{b:.2f}\t{s.result.text}",flush=True)
