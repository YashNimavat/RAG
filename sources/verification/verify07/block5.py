def take_within_budget(ranked_ids: list[str], n_tokens: dict[str, int], budget: int) -> tuple[list[str], int]:
    """Walk the ranked list; keep chunks while the running token total stays within `budget`."""
    kept, used = [], 0
    for cid in ranked_ids:
        if used + n_tokens[cid] > budget:
            break
        kept.append(cid)
        used += n_tokens[cid]
    return kept, used
