"""Prompt Builder.

Turns the structured Kubernetes evidence from the investigation layer into a
deterministic prompt for an LLM acting as a Senior Kubernetes SRE.
"""

import json

SYSTEM_PROMPT = """You are a Senior Kubernetes SRE diagnosing a Kubernetes incident.

You are given structured troubleshooting evidence: pod statuses, log highlights,
cluster events, deployment health, and networking findings.

Analyze the evidence by CORRELATING signals across all sections. Do not simply
repeat log lines. Reason like an engineer: identify the failure, what caused it,
and how to fix it.

Respond with ONLY a JSON object with exactly these keys:
{
  "root_cause": "short, specific root cause (one sentence)",
  "explanation": "detailed reasoning that connects the evidence to the root cause",
  "fix": "specific, actionable fix instructions",
  "kubectl_commands": ["list of concrete kubectl commands to run"],
  "prevention": "how to prevent this class of failure in the future",
  "confidence": 92
}

Rules:
- Confidence is an integer 0-100 reflecting how sure you are, based on the evidence.
- If the cluster shows no problems, state that in "root_cause" and use confidence <= 60.
- Prioritize current pod readiness, deployment availability, and recent events over historical log lines.
- A container's lastState and logs fetched with --previous describe an earlier container run, not necessarily an active failure. If the current container is Running and Ready, report prior errors as historical/transient unless current evidence confirms recurrence.
- Do not claim the API server or control plane is currently unavailable when kubectl successfully collected current cluster evidence and current health checks are healthy.
- If current workloads are healthy and there are no recent warning events, explicitly say there is no active issue; do not recommend restarting healthy components based only on old log errors.
- If evidence is missing or empty, say so instead of guessing.
- Be specific and Kubernetes-aware. Avoid generic advice.
- Output valid JSON only, no markdown fences."""


def _compact(value, max_items: int = 10, max_str: int = 400) -> object:
    """Recursively trim lists, dicts, and long strings to keep the prompt small."""
    if isinstance(value, dict):
        return {key: _compact(item, max_items, max_str) for key, item in list(value.items())[:max_items]}
    if isinstance(value, list):
        trimmed = [_compact(item, max_items, max_str) for item in value[:max_items]]
        if len(value) > max_items:
            trimmed.append(f"... and {len(value) - max_items} more")
        return trimmed
    if isinstance(value, str) and len(value) > max_str:
        return value[:max_str] + "..."
    return value


def build_user_prompt(evidence: dict) -> str:
    """Render the evidence payload into the user section of the prompt."""
    compact = _compact(evidence)
    return f"Kubernetes troubleshooting evidence:\n\n{json.dumps(compact, indent=2, default=str)}"


def build_messages(evidence: dict) -> list[dict]:
    """Return the full message list (system + user) for the LLM call."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_prompt(evidence)},
    ]
