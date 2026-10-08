import re,sys,glob
L=open(sys.argv[1],encoding='utf-8').read()
book=" ".join(open(f,encoding='utf-8').read() for f in glob.glob(sys.argv[2]+'/*.txt'))
book=re.sub(r'\s+',' ',book).lower()
# n-gram overlap: any 9-word window of lesson prose found verbatim in book
words=re.findall(r"[a-z0-9']+",L.lower())
bw=" ".join(re.findall(r"[a-z0-9']+",book))
hits=set()
for i in range(len(words)-8):
    g=" ".join(words[i:i+9])
    if g in bw: hits.add(g)
for h in sorted(hits): print(h)
