import sherpa_onnx, soundfile as sf, sys
D="/tmp/asr/sherpa-onnx-whisper-large-v3/"
r=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=D+"large-v3-encoder.int8.onnx",decoder=D+"large-v3-decoder.int8.onnx",tokens=D+"large-v3-tokens.txt",language="ar",task="transcribe",num_threads=8)
x,sr=sf.read(sys.argv[1],dtype="float32")
for a in sys.argv[2:]:
    a,b=map(float,a.split(","))
    s=r.create_stream(); s.accept_waveform(sr,x[int(a*sr):int(b*sr)]); r.decode_stream(s)
    print(f"{a:.2f}-{b:.2f}\t{s.result.text}",flush=True)
