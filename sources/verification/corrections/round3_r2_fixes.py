"""Fixes for Codex re-review 2 minor findings R2-01 and R2-02 (2026-10-08), applied to contracts_check.py.
Run from this folder: python -I round3_r2_fixes.py   (edits contracts_check.py in place; each replacement must match once)."""
import pathlib

p = pathlib.Path("contracts_check.py")
raw = p.read_bytes()
crlf = b"\r\n" in raw
t = raw.decode("utf-8").replace("\r\n", "\n")


def rep(a, b):
    global t
    n = t.count(a)
    assert n == 1, (n, a[:80])
    t = t.replace(a, b)
    print("ok", ascii(a[:60]))


# R2-01: cleaning.steps (and every nested parser/cleaning field) is required
rep('PARSER_REQUIRED = ("backend", "version", "call", "options")',
    'PARSER_REQUIRED = ("backend", "version", "call", "options")\n'
    'CLEANING_REQUIRED = ("version", "steps")   # R2-01: every nested cleaning field in the 06 §5.3 manifest is required')
rep('    miss += ["cleaning.version"] if "version" not in man.get("cleaning", {}) else []',
    '    miss += [f"cleaning.{k}" for k in CLEANING_REQUIRED if k not in man.get("cleaning", {})]   # R2-01')
rep('''    check("R-02", f"each missing manifest field rejected ({len(MANIFEST_REQUIRED) + len(DOC_REQUIRED) + len(ROW_REQUIRED)} fields)",
          not miss_man, str(miss_man))''',
    '''    for grp, keys in (("parser", PARSER_REQUIRED), ("cleaning", CLEANING_REQUIRED)):   # R2-01: nested fields
        for k in keys:
            m2 = json.loads(mb)
            del m2[grp][k]
            b2 = manifest_bytes(m2)                       # digest recomputed over the mutated bytes
            if not raises(BindingError, validate_binding, make_header(b2, man["snapshot_id"]), b2, {"climate": pages}):
                miss_man.append(f"{grp}.{k}")
    n_fields = len(MANIFEST_REQUIRED) + len(DOC_REQUIRED) + len(ROW_REQUIRED) + len(PARSER_REQUIRED) + len(CLEANING_REQUIRED)
    check("R-02", f"each missing manifest field rejected, nested parser/cleaning fields included ({n_fields} fields)",
          not miss_man, str(miss_man))
    m_steps = json.loads(mb); del m_steps["cleaning"]["steps"]; b_steps = manifest_bytes(m_steps)
    check("R2-01", "manifest without cleaning.steps (digest recomputed) raises BindingError before translation",
          raises(BindingError, load_dataset, [bad_gold], make_header(b_steps, man["snapshot_id"]), b_steps,
                 {"climate": pages}, snap.snapshot_id))
    check("R2-01", "valid manifest with cleaning {version: none, steps: []} still passes",
          man["cleaning"] == {"version": "none", "steps": []} and validate_binding(header, mb, {"climate": pages}) is not None)''')

# R2-02: undefined kappa (point or every resample) returns an explicit undefined result instead of IndexError
rep('''    ks.sort()
    return cohens_kappa(r1, r2), (ks[int(0.025 * (len(ks) - 1))], ks[int(0.975 * (len(ks) - 1))]), undefined''',
    '''    point = cohens_kappa(r1, r2)
    if point is None or not ks:   # R2-02: kappa undefined (e.g. constant identical labels) -> no interval, no certification
        return point, None, undefined
    ks.sort()
    return point, (ks[int(0.025 * (len(ks) - 1))], ks[int(0.975 * (len(ks) - 1))]), undefined''')
rep('''    kc, (clo, chi), _ = kappa_bootstrap(cl_h, cl_j, clusters=cl_a, n_boot=500, seed=1, _trace=trk)''',
    '''    kc, (clo, chi), _ = kappa_bootstrap(cl_h, cl_j, clusters=cl_a, n_boot=500, seed=1, _trace=trk)
    ku, ku_ci, ku_undef = kappa_bootstrap([1] * 60, [1] * 60, n_boot=2000, seed=0)   # R2-02 reproduction
    check("R2-02", "constant identical labels: kappa undefined -> explicit (None, None, n_undefined), no IndexError",
          ku is None and ku_ci is None and ku_undef == 2000, f"point={ku} ci={ku_ci} undefined={ku_undef}")''')

if crlf:
    t = t.replace("\n", "\r\n")
p.write_bytes(t.encode("utf-8"))
print("written")
