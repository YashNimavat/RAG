import re,sys,pathlib
t=open(sys.argv[1],encoding='utf-8').read()
blocks=re.findall(r'```python\n(.*?)```',t,re.S)
out=pathlib.Path(sys.argv[2])
for i,b in enumerate(blocks):
    (out/f'block{i}.py').write_text(b,encoding='utf-8')
    print(i,len(b.splitlines()),b.splitlines()[0][:80])
