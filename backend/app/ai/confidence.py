"""Confidence Engine.

Scores how confident we are in a diagnosis by blending the model's self-assessed
confidence with corroborating signals from the collected evidence. If the
evidence disagrees (or is empty), the score is capped accordingly.
"""

# (section, key, weight, human-readable reason)
EVIDENCE_SIGNALS = [
    ("pods", "problematic_pods", 35, "Pod(s) in a failing state"),
    ("logs", "collected", 15, "Relevant log highlights collected"),
    ("events", "findings", 20, "Warning events found"),
    ("deployments", "unhealthy_deployments", 25, "Unhealthy deployment(s)"),
    ("network", "findings", 20, "Networking findings"),
]


def _evidence_strength(evidence: dict) -> int:
    """0-100 signal of how much corroborating evidence exists."""
    strength = 0
    for section, key, weight, _label in EVIDENCE_SIGNALS:
        items = (evidence.get(section) or {}).get(key)
        if items:
            strength += weight
    return min(100, strength)


def evidence_reasoning(evidence: dict) -> list[str]:
    """Human-readable reasons derived from which evidence sections are populated."""
    return [
        label
        for section, key, _weight, label in EVIDENCE_SIGNALS
        if (evidence.get(section) or {}).get(key)
    ]


def compute_confidence(evidence: dict, model_confidence: int | None) -> tuple[int, list[str]]:
    """Return (confidence 0-100, list of reasoning strings)."""
    strength = _evidence_strength(evidence)
    reasons = evidence_reasoning(evidence)

    if model_confidence is None:
        score = strength or 50
        reasons = reasons or ["No clear failure signals in the collected evidence"]
    elif strength == 0:
        # The model claims a problem but we found no corroborating evidence.
        score = min(model_confidence, 60)
        reasons = reasons or ["No clear failure signals in the collected evidence"]
    else:
        score = round(0.6 * model_confidence + 0.4 * strength)

    return max(0, min(100, score)), reasons
