import numpy as np, wave, sys
def load(fn):
    w=wave.open(fn); sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(float)/32768
    if w.getnchannels()==2: x=x.reshape(-1,2).mean(1)
    return x,sr
def f0(x,sr):
    fl=int(0.04*sr); hop=int(0.01*sr); out=[]
    for i in range(0,len(x)-fl,hop):
        fr=x[i:i+fl]*np.hanning(fl)
        if np.sqrt((fr**2).mean())<0.02: continue
        ac=np.correlate(fr,fr,'full')[fl-1:]
        lo,hi=int(sr/300),int(sr/60)
        k=lo+np.argmax(ac[lo:hi])
        if ac[k]/ac[0]>0.45: out.append(sr/k)
    return np.array(out)
def speech_bounds(x,sr,thr=0.01):
    e=np.sqrt(np.convolve(x**2,np.ones(int(0.02*sr))/int(0.02*sr),'same'))
    idx=np.where(e>thr)[0]
    return idx[0]/sr, idx[-1]/sr
for n in sys.argv[1:]:
    x,sr=load(n); p=f0(x,sr); a,b=speech_bounds(x,sr)
    print(n, 'dur %.2f speech %.2f-%.2f'%(len(x)/sr,a,b), 'f0 med %.0f p10 %.0f p90 %.0f'%(np.median(p),np.percentile(p,10),np.percentile(p,90)), 'peak %.2f rms %.3f'%(np.abs(x).max(), np.sqrt((x**2).mean())))
