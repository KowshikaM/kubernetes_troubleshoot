"""Pod inspection: gather pod status and detect unhealthy pods."""

from datetime import datetime, timezone

from loguru import logger

from app.kubernetes.kubectl import KubectlExecutor, namespace_args

# Waiting/terminated reasons that indicate a problem in a container.
UNHEALTHY_REASONS = {
    "CrashLoopBackOff",
    "ImagePullBackOff",
    "ErrImagePull",
    "OOMKilled",
    "CreateContainerConfigError",
    "CreateContainerError",
    "RunContainerError",
    "Error",
    "Unknown",
}

# A container stuck in ContainerCreating for longer than this is a problem.
STUCK_CONTAINER_CREATING_SECONDS = 120


class PodInspector:
    """Inspects pods and flags the ones that need attention."""

    def __init__(self, kubectl: KubectlExecutor) -> None:
        self.kubectl = kubectl

    def inspect(self, namespace: str | None = None) -> dict:
        """Return a summary of pods plus the unhealthy ones."""
        result = self.kubectl.run("get", "pods", *namespace_args(namespace), "-o", "json")
        if not result.success:
            logger.error("failed to list pods: {}", result.error)
            return {
                "healthy": True,
                "pod_count": 0,
                "error": result.error,
                "problematic_pods": [],
            }

        items = (result.output_json() or {}).get("items", [])
        problematic_pods = [issue for pod in items if (issue := self._detect_issue(pod))]

        return {
            "healthy": len(problematic_pods) == 0,
            "pod_count": len(items),
            "problematic_pods": problematic_pods,
        }

    def _detect_issue(self, pod: dict) -> dict | None:
        """Return an issue summary for a pod, or None when it looks healthy."""
        metadata = pod.get("metadata", {})
        status = pod.get("status", {})
        name = metadata.get("name", "unknown")
        namespace = metadata.get("namespace", "default")
        phase = status.get("phase", "")
        containers = status.get("containerStatuses", [])
        pod_is_old = self._pod_is_old(metadata)

        issues = []
        container_waiting_reasons = []

        for container in containers:
            state = container.get("state", {})
            last_state = container.get("lastState", {})

            waiting_reason = state.get("waiting", {}).get("reason", "")
            waiting_message = state.get("waiting", {}).get("message", "")
            terminated_reason = state.get("terminated", {}).get("reason", "")
            last_terminated_reason = last_state.get("terminated", {}).get("reason", "")
            restarts = container.get("restartCount", 0)
            currently_healthy = bool(state.get("running")) and container.get("ready", False)

            if waiting_reason in UNHEALTHY_REASONS:
                issues.append({
                    "reason": waiting_reason,
                    "message": waiting_message,
                    "restarts": restarts,
                })
            if terminated_reason in {"OOMKilled", "Error"}:
                issues.append({"reason": terminated_reason, "message": "", "restarts": restarts})
            if last_terminated_reason in {"OOMKilled", "Error"} and not currently_healthy:
                issues.append({"reason": last_terminated_reason, "message": "", "restarts": restarts})
            container_waiting_reasons.append(waiting_reason)

        if phase == "Pending" and not issues:
            if "ContainerCreating" in container_waiting_reasons:
                # A container that is still creating is normal at startup; it is
                # only a problem when it stays stuck for a while.
                if pod_is_old:
                    issues.append({
                        "reason": "ContainerCreating (stuck)",
                        "message": "Pod has been stuck in ContainerCreating",
                        "restarts": 0,
                    })
            elif pod_is_old:
                issues.append({
                    "reason": "Pending",
                    "message": "Pod is stuck in Pending (unscheduled or waiting on resources)",
                    "restarts": 0,
                })
        elif phase == "Unknown":
            issues.append({"reason": "Unknown", "message": "Pod status cannot be determined", "restarts": 0})
        elif phase == "Failed":
            issues.append({"reason": "Error", "message": "Pod has failed", "restarts": 0})

        if not issues:
            return None

        primary = issues[0]
        return {
            "name": name,
            "namespace": namespace,
            "status": primary["reason"],
            "phase": phase,
            "restarts": max(issue["restarts"] for issue in issues),
            "message": (primary["message"] or "").strip()[:300],
            "reasons": issues,
        }

    @staticmethod
    def _pod_is_old(metadata: dict) -> bool:
        """Return True when the pod has existed longer than the stuck threshold."""
        created = metadata.get("creationTimestamp")
        if not created:
            return False
        try:
            created_at = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except ValueError:
            return False
        age = datetime.now(timezone.utc) - created_at
        return age.total_seconds() > STUCK_CONTAINER_CREATING_SECONDS
