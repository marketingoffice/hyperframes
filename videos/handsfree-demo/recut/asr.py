"""Word-level transcript with local Parakeet (sherpa-onnx). Usage: python3 asr.py in.wav out.json"""
import sys, json, numpy as np, librosa, sherpa_onnx
M = "/tmp/claude-0/hf/sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8"
rec = sherpa_onnx.OfflineRecognizer.from_transducer(
    encoder=f"{M}/encoder.int8.onnx", decoder=f"{M}/decoder.int8.onnx", joiner=f"{M}/joiner.int8.onnx",
    tokens=f"{M}/tokens.txt", model_type="nemo_transducer", num_threads=4)
y, sr = librosa.load(sys.argv[1], sr=16000)
db = librosa.amplitude_to_db(librosa.feature.rms(y=y, frame_length=400, hop_length=160)[0])
sp = db > np.percentile(db, 30) + 10
# speech regions merged over gaps < 0.6 s, chunked <= 20 s
regs, i, n = [], 0, len(sp)
while i < n:
    if sp[i]:
        j = i
        while j < n and (sp[j] or sp[j:j + 60].any()): j += 1
        regs.append([max(0, i - 15), min(n, j + 15)]); i = j
    else: i += 1
chunks = []
for a, b in regs:
    while b - a > 2000:
        # split at quietest frame in 15-20 s window
        k = a + 1500 + int(np.argmin(db[a + 1500:a + 2000])); chunks.append((a, k)); a = k
    chunks.append((a, b))
words = []
for a, b in chunks:
    s = rec.create_stream(); s.accept_waveform(16000, y[a * 160:b * 160]); rec.decode_stream(s)
    r = s.result; toks, ts = r.tokens, r.timestamps
    cur = None
    for t, st in zip(toks, ts):
        st = a / 100 + st
        if t.startswith(" ") or cur is None:
            if cur: words.append(cur)
            cur = {"w": t.strip(), "s": round(st, 2), "e": round(st + 0.08, 2)}
        else:
            cur["w"] += t; cur["e"] = round(st + 0.08, 2)
    if cur: words.append(cur)
json.dump(words, open(sys.argv[2], "w"))
print(len(chunks), "chunks", len(words), "words")
