"""Item 4/5 follow-up: what happens when chunk_overlap == chunk_size (accepted by both validators)?
Each case runs in a child process with a timeout so a non-terminating split cannot hang the lab.
Run: python -I lab04b_equal_overlap.py
"""
import multiprocessing as mp

TEXT = " ".join(f"word{i:03d}" for i in range(60))  # 60 words x 8 chars incl. space = 479 chars


def lc_case(q):
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    sp = RecursiveCharacterTextSplitter(chunk_size=40, chunk_overlap=40)
    out = sp.split_text(TEXT)
    q.put(f"LangChain size=40 overlap=40: {len(out)} chunks; first 3 = {out[:3]}")


def li_case(q):
    from llama_index.core.node_parser import SentenceSplitter
    sp = SentenceSplitter(chunk_size=40, chunk_overlap=40)
    out = sp.split_text(TEXT)
    q.put(f"LlamaIndex size=40 overlap=40: {len(out)} chunks; first 2 = {out[:2]}")


if __name__ == "__main__":
    print("TEXT length:", len(TEXT))
    for fn in (lc_case, li_case):
        q = mp.Queue()
        p = mp.Process(target=fn, args=(q,))
        p.start()
        p.join(60)
        if p.is_alive():
            p.terminate()
            print(f"{fn.__name__}: did not finish within 60 s (terminated)")
        else:
            print(q.get() if not q.empty() else f"{fn.__name__}: exit code {p.exitcode}, no result")
