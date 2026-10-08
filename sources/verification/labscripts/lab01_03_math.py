"""Items 1-3: boundary-containment probability, chunk-count formula, dilution toy cosines.
Pure Python + NumPy. Run: python -I lab01_03_math.py
"""
import math
import sys

import numpy as np


def fixed_window_spans(L, S, O):
    """Character spans [start, end) of a plain fixed-window chunker (last window may be short)."""
    assert 0 <= O < S
    stride = S - O
    spans, start = [], 0
    while True:
        end = min(start + S, L)
        spans.append((start, end))
        if end >= L:
            break
        start += stride
    return spans


def p_contained_formula(S, O, F):
    return min(1.0, (S - F + 1) / (S - O))


def p_contained_bruteforce(L, S, O, F, interior_only=True):
    """Fraction of span start positions p (span = [p, p+F)) wholly inside >=1 chunk."""
    spans = fixed_window_spans(L, S, O)
    starts = range(0, L - F + 1)
    if interior_only:  # avoid edge effects; whole number of strides => exact uniform phase
        stride = S - O
        n_periods = (L - 3 * S) // stride
        starts = range(S, S + n_periods * stride)
    hit = total = 0
    for p in starts:
        total += 1
        # chunk k can contain [p, p+F) only if start_k <= p; check the few candidates near p
        k_hi = p // (S - O)
        ok = False
        for k in range(max(0, k_hi - S // (S - O) - 1), min(len(spans), k_hi + 1)):
            a, b = spans[k]
            if a <= p and p + F <= b:
                ok = True
                break
        hit += ok
    return hit / total, hit, total


def p_contained_exhaustive(L, S, O, F):
    """Same but with no shortcut (checks every chunk) on a smaller L, all start positions."""
    spans = fixed_window_spans(L, S, O)
    hit = total = 0
    for p in range(0, L - F + 1):
        total += 1
        hit += any(a <= p and p + F <= b for a, b in spans)
    return hit / total, hit, total


def main():
    print("python", sys.version.split()[0], "numpy", np.__version__)
    print("\n=== Item 1: P(span of length F wholly inside >=1 chunk) ===")
    S, F = 1000, 500
    for O in (0, 200, 400):
        f = p_contained_formula(S, O, F)
        bf, hit, tot = p_contained_bruteforce(200_000, S, O, F)
        ex, eh, et = p_contained_exhaustive(20_000, S, O, F)
        print(f"S={S} F={F} O={O}: formula={f:.6f}  brute(interior,L=200000)={bf:.6f} ({hit}/{tot})"
              f"  exhaustive(all starts,L=20000)={ex:.6f} ({eh}/{et})")
    print("Guarantee threshold check (P==1 iff F <= O+1), S=1000, O=200:")
    for F in (200, 201, 202, 250):
        bf, hit, tot = p_contained_bruteforce(50_000, 1000, 200, F)
        print(f"  F={F}: formula={p_contained_formula(1000, 200, F):.6f} brute={bf:.6f}")

    print("\n=== Item 2: number of chunks ceil((L-O)/(S-O)) for L > S ===")
    for S, O in ((1000, 200), (300, 60), (300, 0), (500, 100)):
        mism = 0
        for L in range(S + 1, 20 * S):
            n_impl = len(fixed_window_spans(L, S, O))
            n_formula = math.ceil((L - O) / (S - O))
            mism += n_impl != n_formula
        print(f"S={S} O={O}: checked L={S+1}..{20*S-1}, mismatches={mism}")
    for L in (1001, 1800, 1801, 5000, 73536):
        S, O = 1000, 200
        sp = fixed_window_spans(L, S, O)
        stored = sum(b - a for a, b in sp)
        print(f"  L={L} S=1000 O=200: impl={len(sp)} formula={math.ceil((L-O)/(S-O))}"
              f" stored_chars/L={stored/L:.3f} (S/(S-O)={S/(S-O):.3f})")

    print("\n=== Item 3: dilution toy (chunk vector = mean of sentence vectors) ===")
    q = np.array([1.0, 0.0])
    r, u = np.array([1.0, 0.0]), np.array([0.0, 1.0])

    def cos(a, b):
        return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))

    comp = np.array([0.6, 0.8])
    print(f"competitor c=[0.6,0.8]: cos(q,c)={cos(q, comp):.3f}")
    for n in range(0, 5):
        chunk = np.mean(np.vstack([r] + [u] * n), axis=0)
        c = cos(q, chunk)
        print(f"n={n} off-topic: chunk={np.round(chunk, 4).tolist()} cos={c:.3f}"
              f" 1/sqrt(1+n^2)={1/math.sqrt(1+n*n):.3f} beats_competitor={c > cos(q, comp)}")


if __name__ == "__main__":
    main()
