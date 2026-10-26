"""Investigation service: orchestrates Kubernetes evidence collection.

Acts like a junior DevOps engineer gathering debugging evidence before any
AI reasoning happens: pods -> logs -> events -> deployments -> networking.
"""

from loguru import logger

from app.core.config import get_settings
from app.kubernetes.deployments import DeploymentInspector
from app.kubernetes.events import EventsAnalyzer
from app.kubernetes.kubectl import KubectlExecutor
from app.kubernetes.logs import LogsCollector
from app.kubernetes.network import NetworkInspector
from app.kubernetes.pods import PodInspector
from app.services.insforge_client import get_insforge_client


class InvestigationService:
    """Runs the full evidence-collection flow and returns structured evidence."""

    def __init__(
        self,
        kubectl_bin: str | None = None,
        kubeconfig_path: str | None = None,
        kubectl_timeout: int | None = None,
        context: str | None = None,
    ) -> None:
        settings = get_settings()
        self.kubectl = KubectlExecutor(
            kubectl_bin=kubectl_bin or settings.KUBECTL_BIN,
            kubeconfig_path=kubeconfig_path or settings.KUBECONFIG_PATH,
            timeout=kubectl_timeout or settings.KUBECTL_TIMEOUT_SECONDS,
            context=context or None,
        )
        self.pods = PodInspector(self.kubectl)
        self.logs = LogsCollector(self.kubectl)
        self.events = EventsAnalyzer(self.kubectl)
        self.deployments = DeploymentInspector(self.kubectl)
        self.network = NetworkInspector(self.kubectl)

    def investigate(self, namespace: str | None = None, channel: str | None = None) -> dict:
        """Collect Kubernetes evidence and return it as a structured payload.

        If a realtime channel (e.g., user id) is provided, publish step-by-step progress
        updates so the frontend can stream live status.
        """
        insforge = None
        if channel:
            try:
                insforge = get_insforge_client()
            except Exception:
                insforge = None

        if not self.kubectl.is_available():
            logger.error("kubectl is not available on this machine")
            if insforge:
                try:
                    insforge.publish_progress(channel, {"type": "error", "message": "kubectl not found"})
                except Exception:
                    pass
            return {
                "status": "unavailable",
                "error": "kubectl binary not found. Install kubectl or set KUBECTL_BIN / KUBECONFIG_PATH.",
                "investigation": {},
            }

        if not self.kubectl.is_cluster_reachable():
            logger.error("kubectl is installed but no cluster is reachable")
            if insforge:
                try:
                    insforge.publish_progress(channel, {"type": "error", "message": "cluster unreachable"})
                except Exception:
                    pass
            return {
                "status": "error",
                "error": "kubectl is installed but no cluster is reachable. Check your kubeconfig and cluster state.",
                "investigation": {},
            }

        logger.info("starting Kubernetes investigation (namespace={})", namespace or "all")

        # Step 1: Inspect pods
        if insforge:
            try:
                insforge.publish_progress(channel, {"type": "step", "step": "Checking Pods"})
            except Exception:
                pass
        pod_evidence = self.pods.inspect(namespace)

        # Step 2: Collect logs
        if insforge:
            try:
                insforge.publish_progress(channel, {"type": "step", "step": "Reading Logs"})
            except Exception:
                pass
        logs = self.logs.collect(pod_evidence.get("problematic_pods", []))

        # Step 3: Analyze events
        if insforge:
            try:
                insforge.publish_progress(channel, {"type": "step", "step": "Analyzing Events"})
            except Exception:
                pass
        events = self.events.analyze(namespace)

        # Step 4: Inspect deployments
        if insforge:
            try:
                insforge.publish_progress(channel, {"type": "step", "step": "Inspecting Deployments"})
            except Exception:
                pass
        deployments = self.deployments.inspect(namespace)

        # Step 5: Check network
        if insforge:
            try:
                insforge.publish_progress(channel, {"type": "step", "step": "Checking Networking"})
            except Exception:
                pass
        network = self.network.inspect(namespace)

        # Compose evidence
        evidence = {
            "kubectl": {"available": True, "cluster_reachable": True},
            "pods": pod_evidence,
            "logs": logs,
            "events": events,
            "deployments": deployments,
            "network": network,
        }

        # final progress
        if insforge:
            try:
                insforge.publish_progress(channel, {"type": "step", "step": "AI Reasoning"})
            except Exception:
                pass

        return {"status": "success", "investigation": evidence}
