"""Safe wrapper around the kubectl CLI.

Handles command execution, structured output, and graceful failures
without exposing raw subprocess details to the rest of the app.
"""

import json
import os
import subprocess
from dataclasses import dataclass
from typing import Any

from loguru import logger


@dataclass
class KubectlResult:
    """Structured result of a single kubectl invocation."""

    success: bool
    command: str
    stdout: str = ""
    stderr: str = ""
    returncode: int | None = None
    error: str | None = None

    def output_json(self) -> Any:
        """Parse stdout as JSON, or None when it is not valid JSON."""
        if not self.stdout:
            return None
        try:
            return json.loads(self.stdout)
        except json.JSONDecodeError:
            logger.debug("kubectl output was not JSON for: {}", self.command)
            return None


def namespace_args(namespace: str | None) -> list[str]:
    """Return kubectl flags that target one namespace or all namespaces."""
    if namespace:
        return ["--namespace", namespace]
    return ["--all-namespaces"]


class KubectlExecutor:
    """Runs kubectl commands safely and returns structured results."""

    def __init__(
        self,
        kubectl_bin: str = "kubectl",
        kubeconfig_path: str | None = None,
        timeout: int = 30,
        context: str | None = None,
    ) -> None:
        self.kubectl_bin = kubectl_bin
        self.kubeconfig_path = kubeconfig_path or os.environ.get("KUBECONFIG")
        self.timeout = timeout
        self.context = context

    def is_available(self) -> bool:
        """Return True when the kubectl binary exists and reports a client version."""
        return self.run("version", "--client", "--output=yaml").success

    def is_cluster_reachable(self) -> bool:
        """Return True when kubectl can reach a cluster control plane."""
        probe = KubectlExecutor(
            kubectl_bin=self.kubectl_bin,
            kubeconfig_path=self.kubeconfig_path,
            timeout=10,
            context=self.context,
        )
        result = probe.run("get", "--raw=/readyz", "--request-timeout=5s")
        if not result.success:
            logger.warning("no reachable cluster: {}", result.error)
        return result.success

    def run(self, *args: str) -> KubectlResult:
        """Run `kubectl <args>` and return a KubectlResult."""
        command = [self.kubectl_bin]
        if getattr(self, 'context', None):
            command += ["--context", self.context]
        command += list(args)
        env = os.environ.copy()
        if self.kubeconfig_path:
            env["KUBECONFIG"] = self.kubeconfig_path

        try:
            proc = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                env=env,
            )
        except FileNotFoundError:
            logger.error("kubectl binary not found: {}", self.kubectl_bin)
            return KubectlResult(
                success=False,
                command=" ".join(command),
                error=f"kubectl binary not found: {self.kubectl_bin}",
            )
        except subprocess.TimeoutExpired:
            logger.error("kubectl timed out after {}s: {}", self.timeout, " ".join(command))
            return KubectlResult(
                success=False,
                command=" ".join(command),
                error=f"kubectl timed out after {self.timeout}s",
            )

        result = KubectlResult(
            success=proc.returncode == 0,
            command=" ".join(command),
            stdout=proc.stdout.strip(),
            stderr=proc.stderr.strip(),
            returncode=proc.returncode,
        )

        if result.success:
            logger.debug("kubectl ok: {}", result.command)
        else:
            result.error = result.stderr or f"kubectl exited with code {result.returncode}"
            logger.warning("kubectl failed: {} -> {}", result.command, result.error)

        return result
