"""P1 (MC-001 flashcard 'strawberry'): what gpt-oss's tokenizer makes of the word "strawberry".

Tokenizer only: no Groq or Cohere call, no .env read, no model. tiktoken may download an encoding file once.
Uses the same encoding P1 already uses for gpt-oss (P1_FACTS S2: tiktoken.encoding_for_model('gpt-oss-20b') -> o200k_harmony).

Run from rag_learning/ (Git Bash):
    PYTHONIOENCODING=utf-8 uv run python sources/verification/P1/p1_strawberry.py > sources/verification/P1/out_p1_strawberry.txt
Saved output: sources/verification/P1/out_p1_strawberry.txt  (section id S11 in P1_FACTS.md)
"""
import importlib.metadata as md
import sys

import tiktoken

WORD = "strawberry"
QUESTION = "How many r's are in strawberry?"

print("python", sys.version.split()[0], "| tiktoken", md.version("tiktoken"))
print(f"tiktoken.encoding_for_model('gpt-oss-20b') -> {tiktoken.encoding_for_model('gpt-oss-20b').name}")
enc = tiktoken.get_encoding("o200k_harmony")
print(f"encoding {enc.name} n_vocab={enc.n_vocab}")


def pieces(ids):
    return [enc.decode_single_token_bytes(i).decode("utf-8", errors="replace") for i in ids]


print("\n=== S11a the word alone, three ways (what comes right before the word changes the cut)")
for label, text in (("no leading space", WORD), ("leading space", " " + WORD), ("in double quotes", f'"{WORD}"')):
    ids = enc.encode(text)
    print(f"{label:17s} {text!r:16s} -> {len(ids)} tokens  ids={ids}  pieces={pieces(ids)}")

print("\n=== S11b inside the full question")
ids = enc.encode(QUESTION)
text, starts = enc.decode_with_offsets(ids)
assert text == QUESTION
w0 = QUESTION.index(WORD)
w1 = w0 + len(WORD)
print(f"question {QUESTION!r}: {len(ids)} tokens")
word_tokens = []
for k, (i, s) in enumerate(zip(ids, starts)):
    piece = enc.decode_single_token_bytes(i).decode("utf-8", errors="replace")
    e = s + len(piece)
    covers = s < w1 and e > w0                       # this token overlaps the characters of "strawberry"
    if covers:
        word_tokens.append((i, piece))
    print(f"  {k:2d} id={i:<7d} chars[{s:2d},{e:2d}) {piece!r:14s} {'<- part of the word' if covers else ''}")
print(f"the word {WORD!r} (chars [{w0},{w1})) is read as {len(word_tokens)} token(s): "
      f"ids={[i for i, _ in word_tokens]} pieces={[p for _, p in word_tokens]}")

print("\n=== S11c letters vs tokens")
print(f"letter 'r' count in {WORD!r} = {WORD.count('r')} (string count; the model never sees letters, only the IDs above)")
print("DONE")
