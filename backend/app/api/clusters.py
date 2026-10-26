from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from tempfile import NamedTemporaryFile
from typing import List

from app.kubernetes.kubectl import KubectlExecutor
from app.core.config import get_settings
from loguru import logger

router = APIRouter(tags=["clusters"], prefix="/clusters")


class SeedRequest(BaseModel):
    profile: str  # 'good' | 'bad' | 'mixed'
    namespace: str | None = None
    context: str | None = None


@router.get("")
def list_clusters(authorization: str = Header(None)):
    """Return kubeconfig contexts and current context."""
    settings = get_settings()
    ke = KubectlExecutor(kubectl_bin=settings.KUBECTL_BIN, kubeconfig_path=settings.KUBECONFIG_PATH)

    # current context
    current = None
    res_current = ke.run("config", "current-context")
    if res_current.success and res_current.stdout:
        current = res_current.stdout.strip()

    # list contexts
    res = ke.run("config", "get-contexts", "-o", "name")
    if not res.success:
        logger.warning("failed to list contexts: {}", res.error)
        raise HTTPException(status_code=500, detail="Failed to list kubeconfig contexts")

    contexts = [c.strip() for c in res.stdout.splitlines() if c.strip()]
    clusters = []
    for c in contexts:
        clusters.append({"name": c, "current": c == current})

    return {"status": "success", "kubeconfig": settings.KUBECONFIG_PATH, "clusters": clusters}


@router.post("/seed")
def seed_cluster(req: SeedRequest, authorization: str = Header(None)):
    """Seed the selected kubeconfig with test resources.

    profile: good => healthy nginx deployment
             bad  => pod with invalid image to force errors
             mixed => both
    """
    settings = get_settings()
    ke = KubectlExecutor(
        kubectl_bin=settings.KUBECTL_BIN,
        kubeconfig_path=settings.KUBECONFIG_PATH,
        context=req.context,
    )

    ns = req.namespace or "ai-test"

    # create namespace
    r_ns = ke.run("create", "namespace", ns)
    # ignore failure if exists

    yamls: List[str] = []
    if req.profile == "good":
        yamls.append(f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-nginx
  namespace: {ns}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-nginx
  template:
    metadata:
      labels:
        app: test-nginx
    spec:
      containers:
        - name: nginx
          image: nginx:stable
          ports:
            - containerPort: 80
""")
    elif req.profile == "bad":
        yamls.append(f"""
apiVersion: v1
kind: Pod
metadata:
  name: test-bad-pod
  namespace: {ns}
spec:
  containers:
    - name: bad
      image: nonexistent-image-for-testing:latest
      imagePullPolicy: IfNotPresent
""")
    elif req.profile == "mixed":
        # both
        yamls.append(f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: test-nginx
  namespace: {ns}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: test-nginx
  template:
    metadata:
      labels:
        app: test-nginx
    spec:
      containers:
        - name: nginx
          image: nginx:stable
          ports:
            - containerPort: 80
""")
        yamls.append(f"""
apiVersion: v1
kind: Pod
metadata:
  name: test-bad-pod
  namespace: {ns}
spec:
  containers:
    - name: bad
      image: nonexistent-image-for-testing:latest
      imagePullPolicy: IfNotPresent
""")
    else:
        raise HTTPException(status_code=400, detail="Unknown profile")

    outputs = []
    for i, y in enumerate(yamls):
        # write temp file and apply
        with NamedTemporaryFile(mode="w", delete=False, suffix=f"_{i}.yaml") as tf:
            tf.write(y)
            tf.flush()
            path = tf.name
        res = ke.run("apply", "-f", path)
        outputs.append({"yaml_file": path, "success": res.success, "stdout": res.stdout, "stderr": res.stderr})

    return {"status": "success", "namespace": ns, "outputs": outputs}
