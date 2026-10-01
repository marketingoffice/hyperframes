import numpy as np, librosa
from sklearn.mixture import GaussianMixture
y,sr=librosa.load('cvo16.wav',sr=16000)
hop=160
db=librosa.amplitude_to_db(librosa.feature.rms(y=y,frame_length=400,hop_length=hop)[0])
th=np.percentile(db,30)+12
m=db>th; n=len(m)
segs=[];i=0
while i<n:
  if m[i]:
    j=i
    while j<n and (m[j] or m[j:j+25].any()): j+=1
    if j-i>=12: segs.append((i,j))
    i=j
  else:i+=1
mf=librosa.feature.mfcc(y=y,sr=sr,n_mfcc=20,hop_length=hop,n_fft=512)
cen=librosa.feature.spectral_centroid(y=y,sr=sr,hop_length=hop,n_fft=512)[0]
ro=librosa.feature.spectral_rolloff(y=y,sr=sr,hop_length=hop,n_fft=512,roll_percent=0.95)[0]
f0=librosa.yin(y,fmin=70,fmax=350,sr=sr,frame_length=1024,hop_length=hop)
F=[]
for a,b in segs:
  idx=np.arange(a,min(b,mf.shape[1])); idx=idx[m[idx]]
  F.append(np.concatenate([mf[1:,idx].mean(1),[np.median(cen[idx])/1000,np.median(ro[idx])/1000,np.median(f0[idx])/50]]))
F=np.array(F); Z=(F-F.mean(0))/F.std(0)
# supervised: label segments <59 as Hasnain(0) seed
from sklearn.linear_model import LogisticRegression
g=GaussianMixture(2,covariance_type='diag',random_state=0).fit(Z); lab=g.predict(Z)
h=np.bincount(lab[[k for k,(a,b) in enumerate(segs) if b/100<59]]).argmax()
for k,(a,b) in enumerate(segs):
  print(f"{a/100:7.2f} {b/100:7.2f} {'H' if lab[k]==h else 'A'} cen={F[k,-3]:.2f} ro={F[k,-2]:.2f} f0={F[k,-1]*50:.0f} db={np.median(db[a:b][m[a:b]]):.1f}")
