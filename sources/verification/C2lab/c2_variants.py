"""Make broken one-bug variants of the reference solution, run the lab with each (in-process runner), and report
which CHECK cells fail. Variant files and work dirs go to <outdir> (outside the workspace).

Run from rag_learning/:
    uv run python sources/verification/C2lab/c2_variants.py labs/C2_chunking_lab.ipynb <outdir> > sources/verification/C2lab/out_c2_labtest_broken.txt
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
nb, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
os.makedirs(outdir, exist_ok=True)
REF = open(os.path.join(HERE, "c2_solution_ref.py"), encoding="utf-8").read()

CROSS_PAGE = '''def chunk_pages(pages, size, overlap):
    full = "\\n".join(pages)
    starts = [sum(len(x) + 1 for x in pages[:i]) for i in range(len(pages))]
    import bisect
    return [(c.char_start, c.char_end, bisect.bisect_right(starts, c.char_start))
            for c in recursive_chunks(full, size, overlap)]
'''
# name: (intended CHECK, [(old, new), ...]); every `old` must occur exactly once in the reference
VARIANTS = {
    "B1_stride_off_by_one": ("Task 2", [("stride = size - overlap\n", "stride = size - overlap + 1\n")]),
    "B2_overlap_in_pieces_not_chars": ("Task 5", [("if cur[-1][1] - q[0] <= overlap:", "if len(keep) < overlap:")]),
    "B3_chunk_crosses_page": ("Task 6", [(REF[REF.index("def chunk_pages"):REF.index("# == T7")], CROSS_PAGE + "\n")]),
    "B4_ids_uuid": ("Task 7", [('"chunk_id": f"{doc_id}:{snapshot_id}:{h}:{seq:05d}",',
                               '"chunk_id": f"{doc_id}:{snapshot_id}:{h}:{__import__(\'uuid\').uuid4().hex[:5]}",')]),
    "B5_params_hash_builtin_hash": ("Task 7", [('return hashlib.sha256(json.dumps(params, sort_keys=True).encode("utf-8")).hexdigest()[:12]',
                                                'return format(hash(json.dumps(params, sort_keys=True)) & (16 ** 12 - 1), "012x")')]),
    "B6_page_relative_offsets_C2-A-05": ("Task 6", [("out.append((start + c.char_start, start + c.char_end, i + 1))",
                                                    "out.append((c.char_start, c.char_end, i + 1))")]),
    "B7_weak_check_chunks": ("Task 3", [(REF[REF.index("def check_chunks"):REF.index("# == T4p")],
                                         "def check_chunks(text, chunks, size):\n    for c in chunks:\n"
                                         "        assert text[c.char_start:c.char_end] == c.text\n\n")]),
    "B8_no_validation_no_stop_C2-A-04": ("Task 2", [(
        '    if size <= 0:\n        raise ValueError("size must be > 0")\n    if not 0 <= overlap < size:\n'
        '        raise ValueError(f"need 0 <= overlap < size, got overlap={overlap}, size={size}")\n    stride', "    stride"),
        ("        if end == len(text):\n            break\n        start += stride", "        start += stride")]),
    "B9_find_loop_on_empty_separator": ("Task 5", [('    if sep == "":\n        return [(s, s + 1) for s in range(start, end)]\n', "")]),
    "B10_strip_whitespace": ("Task 5", [("return [Chunk(i, text[a:b], a, b) for i, (a, b) in enumerate(spans)]",
                                         "return [Chunk(i, text[a:b].strip(), a, b) for i, (a, b) in enumerate(spans)]")]),
    "B11_record_offsets_page_relative": ("Task 7", [('            "char_start": a,\n            "char_end": b,\n',
                                                     '            "char_start": a - starts[page - 1],\n            "char_end": b - starts[page - 1],\n')]),
}

summary = []
for name, (intended, reps) in VARIANTS.items():
    src = REF
    for old, new in reps:
        assert src.count(old) == 1, (name, old[:60])
        src = src.replace(old, new)
    path = os.path.join(outdir, f"sol_{name}.py")
    open(path, "w", encoding="utf-8").write(src)
    wd = os.path.join(outdir, f"wd_{name}")
    r = subprocess.run([sys.executable, os.path.join(HERE, "c2_lab_runner.py"), nb, path, wd],
                       capture_output=True, text=True, encoding="utf-8", timeout=900)
    out = r.stdout
    fails = re.findall(r"^FAIL cell \d+: # CHECK (Task \d+|save)[^\n]*?<- ([^\n]*)$", out, flags=re.M)
    passes = re.findall(r"^PASS cell \d+: # CHECK (Task \d+|save)", out, flags=re.M)
    failed = [f[0] for f in fails]
    ok = intended in failed
    summary.append((name, intended, ok, failed, len(passes)))
    print(f"### {name}: intended {intended} -> {'FAILS as intended' if ok else 'NOT CAUGHT'}")
    for t, msg in fails:
        print(f"    FAIL {t}: {msg[:160]}")
    print(f"    passed: {', '.join(passes)}")
    if r.returncode:
        print("    runner stderr:", r.stderr[-500:])

print("\n=== summary")
for name, intended, ok, failed, n_pass in summary:
    print(f"{'OK ' if ok else 'BAD'} {name:36s} intended {intended:7s} failed: {', '.join(failed)}  (passed {n_pass})")
print(f"{sum(s[2] for s in summary)}/{len(summary)} variants fail their intended CHECK")
