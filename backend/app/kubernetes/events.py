"""Kubernetes event analysis: surface warning events worth investigating."""

from loguru import logger

from app.kubernetes.kubectl import KubectlExecutor, namespace_args

# Event reasons that indicate a problem in the cluster.
WARNING_REASONS = {
    "FailedScheduling",
    "BackOff",
    "FailedMount",
    "FailedPull",
    "ErrImagePull",
    "Unhealthy",
}


class EventsAnalyzer:
    """Reads cluster events and returns summarized findings."""

    def __init__(self, kubectl: KubectlExecutor) -> None:
        self.kubectl = kubectl

    def analyze(self, namespace: str | None = None) -> dict:
        """Return warning events grouped by (reason, namespace)."""
        args = ["get", "events", *namespace_args(namespace), "-o", "json", "--sort-by=.lastTimestamp"]
        result = self.kubectl.run(*args)

        if not result.success:
            logger.error("failed to list events: {}", result.error)
            return {"count": 0, "warning_reasons_found": [], "findings": [], "error": result.error}

        items = (result.output_json() or {}).get("items", [])
        findings = []
        for event in items:
            reason = event.get("reason", "")
            if reason in WARNING_REASONS:
                involved = event.get("involvedObject", {})
                findings.append({
                    "reason": reason,
                    "type": event.get("type", "Warning"),
                    "namespace": involved.get("namespace", ""),
                    "kind": involved.get("kind", ""),
                    "object": involved.get("name", ""),
                    "message": (event.get("message", "") or "").strip()[:300],
                    "last_seen": event.get("lastTimestamp", ""),
                })

        return {
            "count": len(findings),
            "warning_reasons_found": sorted({finding["reason"] for finding in findings}),
            "findings": self._summarize(findings),
        }

    @staticmethod
    def _summarize(findings: list[dict]) -> list[dict]:
        """Group events by (reason, namespace) into concise summaries."""
        grouped: dict[tuple[str, str], dict] = {}
        for finding in findings:
            key = (finding["reason"], finding["namespace"])
            entry = grouped.setdefault(
                key,
                {
                    "reason": finding["reason"],
                    "namespace": finding["namespace"],
                    "count": 0,
                    "affected_objects": set(),
                    "last_message": "",
                },
            )
            entry["count"] += 1
            if finding["object"]:
                entry["affected_objects"].add(finding["object"])
            if finding["message"]:
                entry["last_message"] = finding["message"]

        summarized = []
        for entry in grouped.values():
            summarized.append({
                "reason": entry["reason"],
                "namespace": entry["namespace"],
                "count": entry["count"],
                "affected_objects": sorted(entry["affected_objects"])[:10],
                "last_message": entry["last_message"][:300],
            })
        return summarized
