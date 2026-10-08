import numpy as np, scipy.io.wavfile as w, sys
SR=44100
music_p, sfxdir, out = sys.argv[1], sys.argv[2], sys.argv[3]
sr,m=w.read(music_p); m=m.astype(float)/32768
def load(n):
    sr,x=w.read(f"{sfxdir}/{n}.wav"); return x.astype(float)/32768
def chime():
    t=np.arange(int(1.6*SR))/SR
    env=np.exp(-t*3.2)*(1-np.exp(-t*400))
    y=(np.sin(2*np.pi*1760*t)+0.7*np.sin(2*np.pi*2349.3*t)+0.25*np.sin(2*np.pi*3520*t))*env*0.35
    return np.stack([y,y],1)
cache={}
def get(n,rate=1.0):
    k=(n,rate)
    if k not in cache:
        x=chime() if n=='chime' else load(n)
        if rate!=1.0:
            idx=np.arange(0,len(x)-1,rate); x=np.stack([np.interp(idx,np.arange(len(x)),x[:,c]) for c in (0,1)],1)
        cache[k]=x
    return cache[k]
def anchor(x,mode):
    a=np.abs(x).mean(1)
    if mode=='peak': return int(np.argmax(a))
    return int(np.argmax(a>0.05*a.max()))
# (time, name, gain dB, anchor, rate)
EV=[
 (0.35,'pop',-14,'on',1.0),
 (2.00,'whoosh',-15,'peak',1.0),
 (2.50,'pop',-14,'on',0.9),
 (3.00,'click',-2,'on',1.0),
 (3.95,'whoosh',-16,'peak',1.15),
 (4.50,'impact-bass-2',-15,'on',1.0),(4.50,'click',-3,'on',0.75),
 (6.00,'key-press',4,'on',1.0),(6.50,'key-press',4,'on',0.94),(7.00,'key-press',4,'on',0.88),
 (7.85,'whoosh',-12,'peak',0.85),
 (9.00,'pop',-12,'on',1.0),
 (9.75,'click',0,'on',1.0),
 (9.95,'whoosh',-11,'peak',1.0),
 (11.20,'click',-10,'on',1.3),
 (11.50,'pop',-15,'on',1.1),
 (12.50,'click',-12,'on',1.4),
 (14.50,'click',-2,'on',1.0),
 (15.00,'click',-2,'on',1.1),
 (15.90,'chime',-4,'on',1.0),
 (18.05,'whoosh',-16,'peak',1.1),(18.30,'whoosh',-19,'peak',1.2),(18.55,'whoosh',-19,'peak',1.3),
 (19.50,'pop',-15,'on',0.85),
 (20.00,'impact-bass-2',-15,'on',1.0),(20.00,'click',-3,'on',0.75),
 (21.90,'whoosh',-14,'peak',1.0),
 (24.00,'key-press',4,'on',1.0),(24.50,'key-press',4,'on',0.94),(25.00,'key-press',4,'on',0.88),
 (25.90,'whoosh',-12,'peak',0.85),
 (26.00,'impact-bass-1',-11,'on',1.0),
]
y=m.copy()
for t,n,g,mode,rate in EV:
    x=get(n,rate)*10**(g/20); s=int(round(t*SR))-anchor(x,mode)
    a=max(0,s); b=min(len(y),s+len(x)); y[a:b]+=x[a-s:b-s]
y*=0.5
w.write(out,SR,(np.clip(y,-1,1)*32767).astype(np.int16))
print('ok',len(y)/SR, 20*np.log10(np.abs(y).max()))
