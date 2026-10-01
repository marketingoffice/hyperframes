import numpy as np, librosa
from sklearn.linear_model import LogisticRegression
y,sr=librosa.load('cvo16.wav',sr=16000); hop=160
db=librosa.amplitude_to_db(librosa.feature.rms(y=y,frame_length=400,hop_length=hop)[0])
mf=librosa.feature.mfcc(y=y,sr=sr,n_mfcc=20,hop_length=hop,n_fft=512)
f0,vf,_=librosa.pyin(y,fmin=70,fmax=350,sr=sr,frame_length=1024,hop_length=hop)
H=[(0.96,59.33),(69.06,72.91),(84.37,87.42),(95.31,96.69),(103.74,105.48),(118.87,125.41),(142.41,150.74),(184.21,206.92),(246.38,262.32)]
A=[(61.09,67.98),(73.66,83.69),(98.10,102.77),(106.48,118.06),(126.65,135.13),(154.05,162.59),(212.43,245.48),(266.05,273.49),(275.6,283.2),(290.08,298.25)]
th=np.percentile(db,30)+12
def fr(rs):
  idx=np.concatenate([np.arange(int(a*100),int(b*100)) for a,b in rs]); return idx[db[idx]>th]
hi,ai=fr(H),fr(A)
# smoothed features (25-frame context mean)
from scipy.ndimage import uniform_filter1d
X=uniform_filter1d(mf[1:],15,axis=1).T
clf=LogisticRegression(max_iter=2000).fit(np.concatenate([X[hi],X[ai]]),np.r_[np.zeros(len(hi)),np.ones(len(ai))])
p=clf.predict_proba(X)[:,1]
np.save('pA.npy',p); np.save('db.npy',db); np.save('f0.npy',np.nan_to_num(f0))
import sys
for a,b in [(150,153),(163,167),(175,179),(207.5,212.5),(226,230),(273,276.5),(283,290),(298,304),(59,62),(87,91),(68,70),(183,185)]:
  s=''
  for t in np.arange(a,b,0.1):
    k=int(t*100); seg=slice(k,k+10)
    if db[seg].max()<th: s+='.'
    else: s+= 'A' if p[seg].mean()>0.5 else 'h'
  print(f"{a:6.1f}-{b:6.1f} {s}")
