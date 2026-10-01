import subprocess,re,json,sys,numpy as np
def chunks(f,total):
    o=subprocess.run(['ffmpeg','-nostdin','-i',f,'-af','silencedetect=n=-40dB:d=0.22','-f','null','-'],capture_output=True,text=True).stderr
    s=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',o)]; e=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',o)]
    pts=[0.0]; ch=[]
    st=0.0
    for a,b in zip(s,e):
        if a>st+0.05: ch.append((st,a))
        st=b
    if total>st+0.05: ch.append((st,total))
    return ch
def dp(ch,lines):
    L=np.array([len(re.sub(r'[^a-z0-9]','',l.lower())) for l in lines],float)
    n,m=len(ch),len(lines)
    tot=sum(b-a for a,b in ch); rate=tot/L.sum()
    INF=1e18; C=np.full((m+1,n+1),INF); B=np.zeros((m+1,n+1),int); C[0,0]=0
    for i in range(1,m+1):
        for j in range(i,n+1):
            for k in range(i-1,j):
                if C[i-1,k]>=INF: continue
                d=ch[j-1][1]-ch[k][0]; ex=L[i-1]*rate
                c=C[i-1,k]+((d-ex)/ (0.3+0.15*ex))**2
                if c<C[i,j]: C[i,j]=c; B[i,j]=k
    out=[]; j=n
    for i in range(m,0,-1):
        k=B[i,j]; out.append((ch[k][0],ch[j-1][1])); j=k
    return out[::-1],rate
f,lines=sys.argv[1],json.load(open(sys.argv[2]))
tot=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout)
ch=chunks(f,tot); print(len(ch),'chunks')
g,rate=dp(ch,lines)
for (a,b),l in zip(g,lines): print(f"{a:6.2f}-{b:6.2f} {b-a:5.2f} exp {len(re.sub(r'[^a-z0-9]','',l.lower()))*rate:5.2f}  {l[:60]}")
json.dump(g,open(sys.argv[3],'w'))
