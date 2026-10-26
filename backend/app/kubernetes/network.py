"""Service / networking inspection: selectors, endpoints, and DNS health."""

from loguru import logger

from app.kubernetes.kubectl import KubectlExecutor, namespace_args


def _selector_matches(selector: dict, labels: dict) -> bool:
    """Return True when the pod labels satisfy every selector key/value pair."""
    return all(labels.get(key) == value for key, value in selector.items())


class NetworkInspector:
    """Checks services and endpoints for connectivity problems."""

    def __init__(self, kubectl: KubectlExecutor) -> None:
        self.kubectl = kubectl

    def inspect(self, namespace: str | None = None) -> dict:
        """Return service/endpoint state plus networking findings."""
        services = self._get_services(namespace)
        endpoints = self._get_endpoints(namespace)
        pods = self._get_pods(namespace)

        if "error" in services or "error" in endpoints or "error" in pods:
            error = services.get("error") or endpoints.get("error") or pods.get("error")
            logger.error("network inspection failed: {}", error)
            return {"service_count": 0, "endpoint_count": 0, "findings": [], "finding_count": 0, "error": error}

        endpoint_map = {
            (endpoint.get("metadata", {}).get("namespace"), endpoint.get("metadata", {}).get("name")): endpoint
            for endpoint in endpoints.get("items", [])
        }
        pod_labels: dict[str, list[dict]] = {}
        for pod in pods.get("items", []):
            metadata = pod.get("metadata", {})
            pod_labels.setdefault(metadata.get("namespace", "default"), []).append(metadata.get("labels") or {})

        service_items = services.get("items", [])

        findings = []
        for service in service_items:
            finding = self._check_service(service, endpoint_map, pod_labels)
            if finding:
                findings.append(finding)

        findings.extend(self._check_dns(endpoint_map, namespace))

        return {
            "service_count": len(service_items),
            "endpoint_count": len(endpoint_map),
            "findings": findings,
            "finding_count": len(findings),
        }

    def _get_services(self, namespace: str | None) -> dict:
        result = self.kubectl.run("get", "services", *namespace_args(namespace), "-o", "json")
        if not result.success:
            logger.error("failed to list services: {}", result.error)
            return {"error": result.error}
        return result.output_json() or {"items": []}

    def _get_endpoints(self, namespace: str | None) -> dict:
        result = self.kubectl.run("get", "endpoints", *namespace_args(namespace), "-o", "json")
        if not result.success:
            logger.error("failed to list endpoints: {}", result.error)
            return {"error": result.error}
        return result.output_json() or {"items": []}

    def _get_pods(self, namespace: str | None) -> dict:
        result = self.kubectl.run("get", "pods", *namespace_args(namespace), "-o", "json")
        if not result.success:
            logger.error("failed to list pods: {}", result.error)
            return {"error": result.error}
        return result.output_json() or {"items": []}

    @staticmethod
    def _check_service(service: dict, endpoint_map: dict, pod_labels: dict[str, list[dict]]) -> dict | None:
        metadata = service.get("metadata", {})
        spec = service.get("spec", {})
        namespace = metadata.get("namespace", "default")
        name = metadata.get("name", "unknown")
        service_type = spec.get("type", "ClusterIP")
        selector = spec.get("selector") or {}

        # ExternalName services resolve via DNS and have no endpoints; skip them.
        if service_type == "ExternalName":
            return None
        if not selector and service_type == "ClusterIP":
            # ClusterIP without selector never gets endpoints (usually headless/typed).
            return None

        endpoint = endpoint_map.get((namespace, name))
        subsets = (endpoint or {}).get("subsets", [])
        addresses = [address for subset in subsets for address in subset.get("addresses", [])]

        if not addresses:
            matching_pods = [labels for labels in pod_labels.get(namespace, []) if _selector_matches(selector, labels)]
            if matching_pods:
                message = (
                    "Service selector matches pods, but none are ready. Check the pods' readiness "
                    "probes and status."
                )
            else:
                message = (
                    "Service selector matches no running pods (possible selector mismatch). Compare "
                    "the service selector with the pod labels."
                )
            return {
                "type": "missing_endpoints",
                "service": name,
                "namespace": namespace,
                "selector": selector,
                "selector_mismatch": not matching_pods,
                "matching_pods": len(matching_pods),
                "message": message,
            }
        return None

    @staticmethod
    def _check_dns(endpoint_map: dict, namespace: str | None) -> list[dict]:
        """Flag core DNS services without ready endpoints (only when scanning the whole cluster)."""
        if namespace:
            return []
        findings = []
        for dns_service in ("kube-dns", "coredns"):
            endpoint = endpoint_map.get(("kube-system", dns_service))
            if endpoint is None:
                continue
            subsets = endpoint.get("subsets", [])
            addresses = [address for subset in subsets for address in subset.get("addresses", [])]
            if not addresses:
                findings.append({
                    "type": "dns",
                    "service": dns_service,
                    "namespace": "kube-system",
                    "message": f"{dns_service} service has no ready endpoints - cluster DNS may be down.",
                })
        return findings
