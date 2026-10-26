"""Fix Recommendation Engine.

Validates the model's suggested fixes and enriches them with concrete kubectl
commands derived from the evidence when the model returns none. Keeps
recommendations practical, Kubernetes-specific, and safe.
"""


def _fallback_commands(evidence: dict) -> list[str]:
    """Build concrete kubectl commands from the evidence when the model is silent."""
    commands: list[str] = []

    for pod in (evidence.get("pods") or {}).get("problematic_pods") or []:
        commands.append(f"kubectl describe pod {pod['name']} -n {pod['namespace']}")
        commands.append(f"kubectl logs {pod['name']} -n {pod['namespace']} --previous")

    for dep in (evidence.get("deployments") or {}).get("unhealthy_deployments") or []:
        commands.append(f"kubectl rollout status deployment/{dep['name']} -n {dep['namespace']}")
        commands.append(f"kubectl edit deployment {dep['name']} -n {dep['namespace']}")

    return commands[:6]


def refine_fix(diagnosis: dict, evidence: dict) -> dict:
    """Ensure kubectl_commands is a sane list; fall back to evidence-derived ones."""
    raw = diagnosis.get("kubectl_commands")
    if not isinstance(raw, list):
        raw = [raw] if raw else []

    commands = [str(cmd).strip() for cmd in raw if str(cmd).strip()]
    if not commands:
        commands = _fallback_commands(evidence)

    diagnosis["kubectl_commands"] = commands[:6]
    return diagnosis
