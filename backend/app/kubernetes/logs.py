"""Log collection for failing pods.

Only relevant lines are kept (exceptions, connection failures, missing
env vars, image failures, startup errors) and the output is capped so we
never return thousands of lines.
"""

import re

from loguru import logger

from app.kubernetes.kubectl import KubectlExecutor

# (compiled pattern, label) pairs used to pick relevant log lines.
LOG_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(?i)\bexception\b|traceback"), "exception"),
    (re.compile(r"(?i)connection (refused|reset|timed out|failed)|econnrefused|network is unreachable"), "connection_failure"),
    (re.compile(r"(?i)env(ironment)? (var|variable).*not set|missing.*(env|var|environment)|required variable|not defined"), "missing_env_var"),
    (re.compile(r"(?i)image pull|manifest unknown|no such image|pull access denied|failed to pull"), "image_failure"),
    (re.compile(r"(?i)failed to start|startup failed|cannot start|initialization failed|panic:"), "startup_error"),
    (re.compile(r"(?i)\bfatal\b|\berror\b"), "error"),
]

MAX_TAIL_LINES = 200
MAX_RELEVANT_LINES = 30
MAX_LINE_LENGTH = 500


class LogsCollector:
    """Fetches concise, relevant logs for the failing pods."""

    def __init__(self, kubectl: KubectlExecutor) -> None:
        self.kubectl = kubectl

    def collect(self, problematic_pods: list[dict]) -> dict:
        """Collect log highlights for each problematic pod."""
        collected = []
        for pod in problematic_pods:
            entry = self._collect_for_pod(pod)
            if entry is not None:
                collected.append(entry)
        return {"count": len(collected), "collected": collected}

    def _collect_for_pod(self, pod: dict) -> dict | None:
        name = pod.get("name")
        namespace = pod.get("namespace")
        if not name:
            return None

        lines = []
        if pod.get("restarts", 0) > 0:
            lines.extend(self._fetch(name, namespace, previous=True))
        lines.extend(self._fetch(name, namespace))

        relevant = self._filter_relevant(lines)

        entry = {
            "pod": name,
            "namespace": namespace,
            "reason": pod.get("status", ""),
            "relevant_lines": relevant,
        }
        if not relevant:
            entry["note"] = "No obviously relevant lines in the recent logs."
        return entry

    def _fetch(self, pod: str, namespace: str, previous: bool = False) -> list[str]:
        args = ["logs", pod, "--namespace", namespace, "--tail", str(MAX_TAIL_LINES), "--timestamps"]
        if previous:
            args.append("--previous")

        result = self.kubectl.run(*args)
        if not result.success:
            logger.warning("could not fetch logs for {}/{}: {}", namespace, pod, result.error)
            return []
        return result.stdout.splitlines()

    def _filter_relevant(self, lines: list[str]) -> list[dict]:
        """Keep the most recent lines that match a known problem pattern."""
        relevant = []
        for line in reversed(lines):
            for pattern, label in LOG_PATTERNS:
                if pattern.search(line):
                    relevant.append({"pattern": label, "line": line.strip()[:MAX_LINE_LENGTH]})
                    break
            if len(relevant) >= MAX_RELEVANT_LINES:
                break
        return relevant
