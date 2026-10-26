"""Deployment inspection: replica counts, rollout state, and conditions."""

from loguru import logger

from app.kubernetes.kubectl import KubectlExecutor, namespace_args


class DeploymentInspector:
    """Checks deployments for availability and rollout problems."""

    def __init__(self, kubectl: KubectlExecutor) -> None:
        self.kubectl = kubectl

    def inspect(self, namespace: str | None = None) -> dict:
        """Return a summary of deployments plus the unhealthy ones."""
        result = self.kubectl.run("get", "deployments", *namespace_args(namespace), "-o", "json")
        if not result.success:
            logger.error("failed to list deployments: {}", result.error)
            return {"deployment_count": 0, "unhealthy_deployments": [], "unhealthy_count": 0, "error": result.error}

        items = (result.output_json() or {}).get("items", [])
        unhealthy = []
        for deployment in items:
            issues = self._detect_issues(deployment)
            if issues:
                unhealthy.append(self._summary(deployment, issues))

        return {
            "deployment_count": len(items),
            "unhealthy_deployments": unhealthy,
            "unhealthy_count": len(unhealthy),
        }

    @staticmethod
    def _detect_issues(deployment: dict) -> list[str]:
        """Return human-readable problems found in a deployment."""
        metadata = deployment.get("metadata", {})
        spec = deployment.get("spec", {})
        status = deployment.get("status", {})
        issues = []

        desired = spec.get("replicas", 0)
        available = status.get("availableReplicas", 0)
        ready = status.get("readyReplicas", 0)
        updated = status.get("updatedReplicas", 0)
        unavailable = status.get("unavailableReplicas", 0)

        if desired > 0 and available < desired:
            issues.append(f"available replicas below desired ({available}/{desired})")
        if ready < desired:
            issues.append(f"ready replicas below desired ({ready}/{desired})")
        if updated < desired:
            issues.append(f"rollout not complete ({updated}/{desired} updated replicas)")
        if unavailable and unavailable > 0:
            issues.append(f"unavailable replicas: {unavailable}")

        observed = status.get("observedGeneration")
        if observed is not None and observed != metadata.get("generation"):
            issues.append("latest spec not yet observed (rollout may be stuck)")

        for condition in status.get("conditions", []):
            condition_type = condition.get("type")
            condition_status = condition.get("status")
            message = (condition.get("message") or "").strip()[:200]
            if condition_type == "Available" and condition_status == "False":
                issues.append(f"Available condition is False: {message}")
            if condition_type == "Progressing" and condition_status == "False":
                issues.append(f"Progressing condition is False: {message}")

        return issues

    @staticmethod
    def _summary(deployment: dict, issues: list[str]) -> dict:
        metadata = deployment.get("metadata", {})
        spec = deployment.get("spec", {})
        status = deployment.get("status", {})
        return {
            "name": metadata.get("name", "unknown"),
            "namespace": metadata.get("namespace", "default"),
            "desired_replicas": spec.get("replicas", 0),
            "available_replicas": status.get("availableReplicas", 0),
            "ready_replicas": status.get("readyReplicas", 0),
            "updated_replicas": status.get("updatedReplicas", 0),
            "unavailable_replicas": status.get("unavailableReplicas", 0),
            "conditions": [
                {
                    "type": condition.get("type"),
                    "status": condition.get("status"),
                    "reason": condition.get("reason"),
                    "message": (condition.get("message") or "")[:200],
                }
                for condition in status.get("conditions", [])
            ],
            "issues": issues,
        }
