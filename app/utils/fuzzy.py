from rapidfuzz import fuzz


def best_fuzzy_match(candidate: str, options: list[str]) -> tuple[str, float]:
    best_option = ""
    best_score = 0.0
    for option in options:
        score = float(fuzz.WRatio(candidate, option))
        if score > best_score:
            best_option = option
            best_score = score
    return best_option, best_score
