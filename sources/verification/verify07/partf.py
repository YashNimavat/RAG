import sys,re
t=open(sys.argv[1],encoding='utf-8').read()
m=re.search(r"```text\n(A bi-encoder.*?)```",t,re.S)
para=" ".join(l.strip() for l in m.group(1).strip().splitlines())
FACT="Tokens beyond the cap are silently dropped before the transformer runs."
print(len(para), para.find(FACT), para.find(FACT)+len(FACT), len(FACT))
sys.path.insert(0,'pkg')
from ragkit._core import fixed_window_chunks, recursive_chunks, chunks_containing
for o in (0,60):
    ch=fixed_window_chunks(para,300,o); print(o,[(c.char_start,c.char_end) for c in ch], chunks_containing(ch,558,629))
ch=recursive_chunks(para,300,60); print('rec',[(c.char_start,c.char_end) for c in ch])
from langchain_text_splitters import RecursiveCharacterTextSplitter as R
d=R(chunk_size=300,chunk_overlap=60,add_start_index=True).create_documents([para])
print('lc',[(x.metadata['start_index'],x.metadata['start_index']+len(x.page_content)) for x in d])
