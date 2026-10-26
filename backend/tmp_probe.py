from app.kubernetes.kubectl import KubectlExecutor
from app.core.config import get_settings
s = get_settings()
ke = KubectlExecutor(kubectl_bin=s.KUBECTL_BIN, kubeconfig_path=s.KUBECONFIG_PATH, timeout=10)
res = ke.run('cluster-info', '--request-timeout=5s')
print('success=', res.success)
print('returncode=', res.returncode)
print('stdout=')
print(res.stdout)
print('stderr=')
print(res.stderr)
