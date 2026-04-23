from dataclasses import dataclass
from models import Plan

# ── Similarity tables ─────────────────────────────────────────────────────────

VIBE_SIMILARITY: dict[tuple[str, str], float] = {
    ("chill",       "social"):      0.7,
    ("social",      "active"):      0.7,
    ("active",      "adventurous"): 0.7,
    ("chill",       "active"):      0.3,
    ("social",      "adventurous"): 0.3,
    ("chill",       "adventurous"): 0.3,
}

# Windows are ordered; adjacency = 1 step apart on the list
_WINDOW_ORDER = ["morning", "afternoon", "evening"]

TIME_COMPATIBILITY: dict[tuple[str, str], float] = {
    ("morning",   "afternoon"): 0.5,
    ("afternoon", "evening"):   0.5,
    ("morning",   "evening"):   0.0,   # opposite ends of the day
}


# ── Output type ───────────────────────────────────────────────────────────────

@dataclass
class MatchResult:
    plan: Plan
    score: float
    explanation: str


# ── Scoring helpers ───────────────────────────────────────────────────────────

def score_activities(a: list[str], b: list[str]) -> float:
    """Jaccard overlap: shared / union."""
    set_a, set_b = set(a), set(b)
    union = set_a | set_b
    if not union:
        return 0.0
    return len(set_a & set_b) / len(union)


def score_vibe(vibe_a: str, vibe_b: str) -> float:
    """1.0 same · 0.7 adjacent · 0.3 distant."""
    if vibe_a == vibe_b:
        return 1.0
    return VIBE_SIMILARITY.get(tuple(sorted([vibe_a, vibe_b])), 0.3)


def score_time(window_a: str, window_b: str) -> float:
    """1.0 same · 0.5 adjacent · 0.0 opposite."""
    if window_a == window_b:
        return 1.0
    return TIME_COMPATIBILITY.get(tuple(sorted([window_a, window_b])), 0.0)


def build_explanation(
    target: Plan,
    candidate: Plan,
    activity_score: float,
    vibe_score: float,
    time_score: float,
) -> str:
    parts = []

    # ── Activities ────────────────────────────────────────────────────────────
    shared = sorted(set(target.activities) & set(candidate.activities))
    if activity_score >= 0.7:
        parts.append(f"You both want to do {', '.join(shared)} — strong overlap.")
    elif shared:
        parts.append(f"You share {', '.join(shared)}.")
    else:
        parts.append("No activity overlap, but other factors align.")

    # ── Vibe ─────────────────────────────────────────────────────────────────
    if vibe_score == 1.0:
        parts.append(f"Same {target.vibe} vibe.")
    elif vibe_score >= 0.7:
        parts.append(f"{target.vibe.capitalize()} and {candidate.vibe} go well together.")
    else:
        parts.append(f"Different vibes ({target.vibe} vs {candidate.vibe}), but could work.")

    # ── Time ─────────────────────────────────────────────────────────────────
    if time_score == 1.0:
        parts.append(f"Both free in the {target.time_window}.")
    elif time_score == 0.5:
        parts.append(
            f"Windows are close ({target.time_window} / {candidate.time_window}) "
            f"— easy to overlap."
        )
    else:
        parts.append(
            f"Different times of day ({target.time_window} vs {candidate.time_window})."
        )

    # ── Group size ────────────────────────────────────────────────────────────
    min_size = min(target.max_group_size, candidate.max_group_size)
    parts.append(f"Group fits up to {min_size}.")

    return " ".join(parts)


# ── Main matching function ────────────────────────────────────────────────────

def match_plans(target: Plan, all_plans: list[Plan], top_n: int = 3) -> list[MatchResult]:
    """
    Score each candidate against the target and return the top matches.

    Weights:  activities 0.5 · vibe 0.3 · time 0.2
    Filters:  same city, same date, different user_id
    """
    results: list[MatchResult] = []

    for candidate in all_plans:
        if candidate.user_id == target.user_id:
            continue
        if candidate.city != target.city:
            continue
        if candidate.date != target.date:
            continue

        activity_score = score_activities(target.activities, candidate.activities)
        vibe_score     = score_vibe(target.vibe, candidate.vibe)
        time_score     = score_time(target.time_window, candidate.time_window)

        final_score = round(
            activity_score * 0.5
            + vibe_score   * 0.3
            + time_score   * 0.2,
            3,
        )

        explanation = build_explanation(
            target, candidate, activity_score, vibe_score, time_score
        )

        results.append(MatchResult(plan=candidate, score=final_score, explanation=explanation))

    return sorted(results, key=lambda r: r.score, reverse=True)[:top_n]
