"""
MedGuard - Fuzzy String Matcher
Wraps RapidFuzz to provide conservative token matching against drug dictionaries.
"""
from typing import Optional
from rapidfuzz import fuzz, process


def match_best_candidate(
    query: str,
    choices: list[str],
    score_cutoff: float = 80.0,
) -> Optional[tuple[str, float]]:
    """
    Finds the best matching string from choices for a given query token.
    Uses token_sort_ratio to remain robust against slight word reorderings or prefixes.

    Returns:
        tuple (matched_choice, score) or None if no choice satisfies score_cutoff.
    """
    if not query or not choices:
        return None

    result = process.extractOne(
        query,
        choices,
        scorer=fuzz.token_sort_ratio,
        score_cutoff=score_cutoff,
    )

    if result is not None:
        matched_str, score, _ = result
        return matched_str, float(score)

    return None
