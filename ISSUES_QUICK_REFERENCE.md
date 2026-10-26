# 🔍 AI Kubernetes Agent - Issues Quick Reference

## 📋 Issue Categories

### 🔴 CRITICAL (4 Issues) - Must Fix Before Deployment

| # | Issue | Problem | Impact | Location |
|---|-------|---------|--------|----------|
| **1** | **Cluster Selection Timing** | Feature added as afterthought at the end | Users can't select different clusters | Line 1449 |
| **2** | **OpenRouter/InsForge Confusion** | Unclear which LLM API to use | Wrong authentication, implementation failures | Lines 641, 829 |
| **3** | **Missing Cluster Selector UI** | Dashboard mockup doesn't include cluster dropdown | Frontend can't display cluster options | Lines 900-1090 |
| **4** | **Prompt Injection Vulnerability** | No input sanitization for logs/pod names | Security risk - LLM could be manipulated | Lines 602-633 |

### 🟠 MAJOR (6 Issues) - Should Fix Soon

| # | Issue | Problem | Impact | Location |
|---|-------|---------|--------|----------|
| **5** | **InsForge Timing** | "DO NOT use" in steps 02-03, but required in step 04 | Confusion, requires refactoring | All prompts |
| **6** | **Filename Typo** | `04-insfoge-backend-prompt.md` (should be `insforge`) | Unprofessional, confusing | Filename |
| **7** | **Realtime Updates Vague** | No specification of event types/payloads/timing | Implementation will be guesswork | Line 935 |
| **8** | **Error Handling Deferred** | Not in steps 02-03, suddenly in step 05 | Breaks "don't modify existing code" rule | Steps 02-05 |
| **9** | **No Namespace Scoping** | Should be cluster-wide or namespace-specific? | Security/compliance issues, info leakage | Lines 55-71 |
| **10** | **Missing User Context** | Early endpoints have no user tracking | Investigation history can't associate with users | Steps 02-03 |

---

## 🚨 Immediate Actions Required

### Before Development Starts:
1. ✅ **Rename file:** `04-insfoge-backend-prompt.md` → `04-insforge-backend-prompt.md`
2. ✅ **Clarify LLM:** Use InsForge LLM gateway OR OpenRouter (not both ambiguously)
3. ✅ **Add cluster selector UI** to the dashboard mockup
4. ✅ **Sanitize inputs** before passing to LLM (pod names, logs, events)

### During Step 2 (Kubernetes Investigation):
- Add error handling for kubectl failures
- Include user_id in API responses (optional, for step 4 integration)

### During Step 3 (AI Reasoning):
- Implement prompt injection prevention
- Filter/escape all Kubernetes data before LLM

### During Step 4 (Dashboard + InsForge):
- **REQUIRED:** Cluster selector dropdown UI
- **REQUIRED:** Define realtime event types and payloads
- Add namespace scoping/RBAC support

### During Step 5 (Integration):
- Comprehensive error handling for all 6 error cases
- Integration testing for multi-cluster scenarios

---

## 🎯 Risk Matrix

```
         Low Impact    Medium Impact   High Impact
High     ─────────────  6,8,9,10      ─────────────
Risk     ─────────────  5,7           ─────────────
         ─────────────  ─────────────  1,2,3,4

Most Critical Zone: Issues 1,2,3,4 (high risk + high impact)
```

---

## 📝 Code Review Checklist

When implementing, verify:

- [ ] Cluster selector UI renders correctly
- [ ] OpenRouter/InsForge integration documented and working
- [ ] All pod names/logs sanitized before LLM calls
- [ ] Realtime events fire at correct times with correct payload
- [ ] Error messages are beginner-friendly
- [ ] Namespace access properly scoped
- [ ] User IDs tracked for investigation history
- [ ] All kubectl errors handled gracefully
- [ ] RBAC considerations documented

---

## 📚 Files Affected

```
Documentation:
├── 04-insfoge-backend-prompt.md        ⚠️ RENAME THIS
├── 01-project-setup-prompt.md          ✓ OK
├── 02-k8s-investigation-engine-prompt.md   ⚠️ Add error handling + user context
├── 03-AI-reasoning-engine-prompt.md    ⚠️ Add prompt injection prevention
└── 05-end-to-end-integration-prompt.md ⚠️ Add cluster selection + realtime spec

Backend Code:
├── api/endpoints                       ⚠️ Add user context tracking
├── kubernetes/                         ✓ Core logic OK
├── ai/prompt_builder.py                ⚠️ Add sanitization
└── services/investigation.py           ⚠️ Add cluster selection logic

Frontend Code:
├── Dashboard.tsx                       ⚠️ Add cluster selector UI
├── components/InvestigationProgress    ✓ OK
├── components/RootCauseCard           ✓ OK
└── hooks/useRealtimeUpdates.ts         ⚠️ Verify realtime payloads
```

---

## 🔗 Dependencies Between Issues

```
Issue 1 (Cluster Selection Timing)
  └─> Blocks Issue 3 (Cluster Selector UI)
       └─> Requires changes to architecture

Issue 2 (OpenRouter Confusion)
  └─> Blocks Issue 4 (Prompt Injection)
       (Need to know which LLM API before sanitizing)

Issue 5 (InsForge Timing)
  └─> Depends on Issue 6 (Filename)
  └─> Blocks Issues 7, 9, 10

Issue 8 (Error Handling)
  └─> Depends on Issues in step 02-03
```

**Suggested Fix Order:** 6 → 1,2 → 3,4 → 5,7 → 8,9,10

---

## 📊 Metrics

- **Total Issues:** 10
- **Critical:** 4 (40%) - Blocks deployment
- **Major:** 6 (60%) - Should fix
- **Lines Affected:** ~3000+ lines across 5 prompt files
- **Estimated Fix Time:** 5-8 hours for experienced team

---

## 💡 Key Insights

1. **Cluster selection** was an afterthought - architectural redesign needed
2. **LLM integration** is ambiguous - architectural clarity required
3. **Security** not considered in AI layer - needs prompt injection prevention
4. **Incremental development** breaks "don't modify existing code" rule
5. **Realtime specification** too vague for reliable implementation

---

**Report Generated:** 2026-08-25
**Analysis by:** Copilot
**Project:** AI Kubernetes Troubleshooting Agent (Abhishek Veeramalla)
