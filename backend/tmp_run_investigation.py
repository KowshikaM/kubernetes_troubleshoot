from app.kubernetes.investigation import InvestigationService

svc = InvestigationService()
res = svc.investigate()
print(res)