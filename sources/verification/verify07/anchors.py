import re,sys,os
root=sys.argv[1]
def slug(h):
    h=h.strip().lower()
    h=re.sub(r'[^\w\- ]','',h)
    return h.replace(' ','-')
src=open(os.path.join(root,'07_SAMPLE_LESSON.md'),encoding='utf-8').read()
links=set(re.findall(r'\]\(([^)#\s]*)#([^)\s]+)\)',src))
for f,a in sorted(links):
    fn=f or '07_SAMPLE_LESSON.md'
    p=os.path.join(root,fn)
    if not os.path.exists(p): print('MISSING FILE',fn,a); continue
    heads=[slug(m) for m in re.findall(r'^#{1,6} (.+)$',open(p,encoding='utf-8').read(),re.M)]
    print('OK  ' if a in heads else 'BAD ',fn,a)
for f in set(re.findall(r'\]\(([^)#\s]+\.md)\)',src)):
    print('file',f,os.path.exists(os.path.join(root,f)))
