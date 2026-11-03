"""Split the one-take narration at its 34 longest pauses -> lines/NN.wav + lines.json (durations)."""
import json, sys, wave
import numpy as np
src, n_lines = sys.argv[1], int(sys.argv[2])
w = wave.open(src); sr = w.getframerate(); ch = w.getnchannels()
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
if ch == 2: x = x.reshape(-1, 2).mean(1)
hop = int(0.01 * sr)
e = np.sqrt(np.array([np.mean(x[i:i + hop] ** 2) for i in range(0, len(x) - hop, hop)]))
quiet = e < 0.004
# runs of silence
runs, i = [], 0
while i < len(quiet):
    if quiet[i]:
        j = i
        while j < len(quiet) and quiet[j]: j += 1
        runs.append((i, j)); i = j
    else: i += 1
inner = [r for r in runs if r[0] > 0 and r[1] < len(quiet)]
cuts = sorted(sorted(inner, key=lambda r: r[1] - r[0], reverse=True)[:n_lines - 1])
print('shortest chosen pause %.2f s, next longest %.2f s' % (min(r[1]-r[0] for r in cuts)/100, sorted([r[1]-r[0] for r in inner], reverse=True)[n_lines-1]/100))
bounds = [0] + [ (a + b) // 2 for a, b in cuts ] + [len(quiet)]
import os; os.makedirs('lines', exist_ok=True)
meta = []
for k in range(n_lines):
    a, b = bounds[k], bounds[k + 1]
    seg = quiet[a:b]
    on = a + int(np.argmax(~seg)); off = b - int(np.argmax(~seg[::-1]))
    s0, s1 = max(0, on * hop - int(0.04 * sr)), min(len(x), off * hop + int(0.12 * sr))
    y = x[s0:s1]
    fade = int(0.01 * sr); y[:fade] *= np.linspace(0, 1, fade); y[-fade:] *= np.linspace(1, 0, fade)
    o = wave.open(f'lines/{k:02d}.wav', 'wb'); o.setnchannels(1); o.setsampwidth(2); o.setframerate(sr)
    o.writeframes((np.clip(y, -1, 1) * 32767).astype(np.int16).tobytes()); o.close()
    meta.append({'i': k, 'dur': round(len(y) / sr, 3)})
json.dump({'sr': sr, 'lines': meta}, open('lines.json', 'w'), indent=1)
print(' '.join('%d:%.2f' % (m['i'], m['dur']) for m in meta))
print('speech total %.1f s' % sum(m['dur'] for m in meta))
