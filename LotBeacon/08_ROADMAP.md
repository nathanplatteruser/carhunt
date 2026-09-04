# 08. MVP, Roadmap, Pilot, Launch Gates

## 1. MVP scope

**One sentence:** for one dealer group, on connected Facebook Pages, LotBeacon ingests Messenger threads, keeps grounded per-customer memory, and gives each rep a prioritized inbox with an editable, fact-checked draft that only a human can send.

### In the MVP

| Capability | Detail |
|---|---|
| Page connect and webhook ingest | Signed, idempotent, replayable |
| Messaging-window state and send checks | Fail-closed rules engine with an explainable block reason |
| Identity and thread model | Page-scoped person, rep ownership, CRM link on customer-supplied identifiers |
| Memory | Working context, rolling summary, six qualifying slots with provenance, commitments ledger |
| Inventory grounding | Feed sync, availability with freshness, structured search, curated spec table |
| Agent runtime | Intent and objection classification, tool plan, fact ledger, constrained generation, fail-closed validator |
| Rep workspace | Prioritized inbox, recap, profile and vehicle panels, next-best-action, editable draft with warnings, send with undo, human-only toggle, escalation |
| Appointments | Real slot offers, two-phase booking, CRM write, confirmation and reminder follow-ups on the permitted message path |
| Review requests | Eligibility from a delivered deal record, neutral non-incentivized ask, one reminder cap, full audit |
| Compliance | Consent and suppression store, opt-out handling, restricted lexicon, audit log |
| Analytics | Event dictionary, pilot dashboard, draft-quality telemetry |
| Safety | Red team and injection suites in CI, kill switch, fallback ladder |

### Explicitly not in the MVP

Auto-send, SMS or email or Instagram or WhatsApp channels, Spanish, payment quoting, trade appraisal beyond an approved vendor range, desking, credit applications, review response management, manager coaching analytics beyond the basic console, self-serve billing.

---

## 2. Roadmap

### Days 0 to 30: foundations and proof of grounding

| Week | Milestones |
|---|---|
| 1 | `DISC-1`, `DISC-3`, `DISC-4` complete. `ARCH-1` scaffold running locally. Meta app submitted for business verification (`META-1`) |
| 2 | `META-2` ingest live in staging. `DATA-1` schema merged. `INV-1` feed ingesting one store. `SEC-1` threat model drafted |
| 3 | `AI-1` orchestrator with `INV-2`/`INV-3` tools. First fact ledger produced end to end. `QA-1` golden set at 100 conversations |
| 4 | `AI-6` validator fail-closed. `QA-3` red team v1 passing. `META-3` send layer with window checks. Internal demo on synthetic threads |

**Day 30 exit:** a synthetic conversation produces a grounded draft, a deliberately injected hallucination is blocked, and no send can bypass the window and suppression checks.

### Days 31 to 60: workspace and shadow mode

| Week | Milestones |
|---|---|
| 5 | `UX-1`, `UX-2`, `UX-3` shipped to staging. `MEM-2`, `MEM-3` live. `CRM-1`, `CRM-2` connected |
| 6 | `UX-4`, `UX-5` with warnings and undo. `WF-2`, `WF-3` playbooks. `CMP-1`, `CMP-2` engine and opt-out |
| 7 | `QA-8` shadow mode on real pilot-store traffic. `CRM-3` calendar integration. `SEC-4` RBAC and SSO |
| 8 | `WF-4` booking end to end. `ANL-1`, `ANL-2` dashboards. `PLT-2` baseline period complete. Shadow results reviewed |

**Day 60 exit:** shadow mode meets its exit criteria (doc 07 layer 2), all P0 compliance and security items are closed, and the pilot analysis plan is pre-registered.

### Days 61 to 90: pilot and hardening

| Week | Milestones |
|---|---|
| 9 | `PLT-3` rep training. Pilot opens with the first matched-pair cohort. `PLT-7` kill switch drilled |
| 10 | `WF-5`, `WF-6` objection playbooks and escalation tuning from real traffic. `PLT-5` feedback triage running |
| 11 | `WF-7` review-request workflow live on the first delivered deals. `QA-6` human review panel weekly. `AI-8` follow-up scheduler |
| 12 | Crossover starts. `SEC-8` penetration test. Mid-pilot readout with the confidence interval on the throughput multiple |

**Day 90 exit:** six weeks of treated data, zero grounded-claim escapes, zero messaging-policy violations, guardrails non-inferior, and a go or no-go recommendation with numbers.

### Beyond 90 days

| Horizon | Focus |
|---|---|
| Q2 | Second dealer group, `DEP-5` onboarding automation, `OPT-1` acceptance loop, manager console |
| Q3 | Selective autonomy for the low-risk intent allowlist (`OPT-5`) behind dealer opt-in, Spanish (`OPT-4`), second channel adapter |
| Q4 | Cost optimization, SOC 2 readiness, marketplace or DMS partner listing |

---

## 3. Pilot design

| Element | Choice |
|---|---|
| Stores | 2 to 3 rooftops in one dealer group, mixed volume, one high-volume and one mid-volume minimum |
| Reps | 12 to 16, matched into pairs on baseline throughput and tenure |
| Duration | 4-week baseline, 6-week treatment, 6-week crossover |
| Assignment | Randomized within matched pairs, stepped-wedge crossover |
| Autonomy | Draft-only for the full pilot. No exceptions |
| Support | Dedicated Slack or Teams channel, 24h triage SLA, weekly review ritual |
| Instrumentation | Full event capture from day one of the baseline, not from the treatment start |
| Exit interview | Structured interviews with every pilot rep and both GMs |
| Reporting | Pre-registered analysis, published internally with the interval, not just the point estimate |

### Pilot-stopping conditions

| Condition | Action |
|---|---|
| Any grounded-claim escape reaching a customer | Global pause, root cause, regression case, restart requires sign-off |
| Any messaging-policy violation | Global pause, policy engine fix, re-verify rules against primary sources |
| Guardrail KPI hard breach at a store | Pause that store, investigate, resume on fix |
| Security incident involving customer data | Global pause, incident response, dealer notification |
| Rep adoption below 60% of eligible threads after week 3 | Not a pause, but a product review: the workspace is losing to the native inbox |

---

## 4. Launch gates

### Gate A: shadow mode to pilot

- [ ] Zero grounded-claim escapes across >= 2,000 shadow drafts
- [ ] Red team and injection suites at 100%
- [ ] All P0 compliance items closed, DPA signed with pilot stores
- [ ] Opt-out end to end verified on every supported path
- [ ] Kill switch drilled and timed under 60 seconds
- [ ] Baseline period complete and accepted by PM and GMs
- [ ] Analysis plan pre-registered with a timestamp
- [ ] Audit log answers "who sent this and why" for any staging message
- [ ] Incident response tabletop completed

### Gate B: pilot to general availability

- [ ] Throughput result reported with a confidence interval, whatever it is
- [ ] All guardrail KPIs non-inferior across the treatment and crossover periods
- [ ] Zero policy violations and zero security incidents in the pilot
- [ ] Penetration test critical and high findings remediated
- [ ] Onboarding automation proven by a non-engineer onboarding two stores
- [ ] Support model meeting response targets for four consecutive weeks
- [ ] Unit economics positive at target price, per `ANL-5`
- [ ] Every `Needs legal review` item in doc 06 resolved or accepted in writing

### Gate C: any autonomy expansion

- [ ] A defined observation period with zero grounded-claim escapes
- [ ] Explicit written dealer opt-in per rooftop
- [ ] Intent allowlist reviewed by legal and the GM
- [ ] Disclosure text approved for jurisdictions where an automated experience talks directly to a customer
- [ ] Auto-send never uses a human-agent messaging path
- [ ] One-click revert to draft-only, drilled

---

## 5. Biggest risks

| # | Risk | Type | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| 1 | A hallucinated price, payment, or availability reaches a customer | Technical | Product-ending trust loss, possible deceptive-practice exposure | Fail-closed validator, restricted classes, human approval, red team at 100%, zero-escape release gate | AAI |
| 2 | Messaging-policy violation costs a dealer their Page messaging | Compliance | Existential for the account | Rules engine with dated policy versions, quarterly re-verification, fail-closed sends | LEG, PLAT |
| 3 | Platform deprecations (message tags, notification types) break follow-ups mid-pilot | Compliance | Broken confirmations and reminders | Template path built first, deprecation watch with a named owner, adapter isolation | INT |
| 4 | Cross-tenant or cross-customer data leak | Security | Catastrophic, likely terminal for the company | Row-level security, adversarial retrieval tests in CI, penetration test | SEC |
| 5 | Inventory feed staleness produces confident wrong availability | Technical | Wasted trips, angry customers | Freshness TTLs, downgrade language, availability contract tests | INT |
| 6 | Review-request workflow drifts into gating or incentives | Compliance | Platform penalties and regulatory exposure | Sentiment features banned from eligibility by test, legal-approved copy, full audit | LEG |
| 7 | Reps ignore the tool and return to the native Page inbox | Adoption | Pilot proves nothing | Coexistence support, mobile triage, training, weekly feedback loop, adoption metric | DS, DES |
| 8 | Rubber-stamping: reps approve without reading | Human factors | Turns a safe design into an unsafe one | Blind-send-rate monitoring, warning discipline, coaching, targeted friction on risky classes | PM |
| 9 | CRM or DMS integration gaps force manual work | Integration | Kills the time savings that produce 4x | Systems inventory before build, contract tests, degraded-mode banners | INT |
| 10 | Underpowered or contaminated pilot | Measurement | Cannot prove or disprove the hypothesis | Power calculation, matched pairs, frozen routing rules, pre-registration | DATA |
| 11 | Model cost or latency makes the unit economics fail | Business | Product cannot be priced | Budget per draft, small-model routing, caching, cost dashboard | AAI |
| 12 | Prompt injection through customer messages or shared listings | Security | Unauthorized tool use or leaked context | Untrusted-content isolation, tool allowlists per intent, injection suite in CI | SEC, AAI |

---

## 6. Top 10 engineering tickets to start tomorrow

| # | Ticket | ID | Team | Why first | Done when |
|---|---|---|---|---|---|
| 1 | Meta app creation, business verification, and Page OAuth connect flow | `META-1` | INT | Verification lead time is the longest pole and it blocks everything downstream | Two pilot Pages connected in staging with encrypted, rotatable tokens |
| 2 | Signed webhook ingest with idempotency and a raw event archive | `META-2` | PLAT | Nothing exists until messages land reliably | 100k-event replay produces zero duplicates, p99 ack under 500ms |
| 3 | Core schema and migrations, including provenance-enforced slots | `DATA-1`, `DATA-2` | PLAT | Every other service depends on the shape of the data | Migrations applied in all environments, unsourced slot write rejected by constraint |
| 4 | Inventory feed sync with availability, freshness, and a normalized vehicle record | `INV-1`, `INV-2` | INT | Grounding is impossible without an authoritative inventory source | Freshness monitor alerting, sold-unit case verified against the DMS |
| 5 | Fact Ledger plus the fail-closed claim validator | `AI-6` | AAI | The core safety mechanism; building it first shapes generation correctly | Injected hallucinations blocked at 100% in the seed red-team suite |
| 6 | Messaging-window and suppression rules engine in the send path | `META-3`, `CMP-1` | PLAT, LEG | A send that bypasses this is an account-ending event | Every synthetic window and suppression scenario passes, blocks are explainable |
| 7 | Orchestrator skeleton with tracing and hard caps | `AI-1` | AAI | Traceability from run one, so nothing is ever unexplainable | Full span tree visible for a run, loop and time caps enforced |
| 8 | Golden conversation set and the CI eval harness | `QA-1`, `QA-2` | QA, AAI | Without evals every later change is a coin flip | 100 conversations scored in CI, merges blocked on regression |
| 9 | Rep workspace shell: prioritized inbox, conversation view, draft editor with warnings | `UX-1`, `UX-2`, `UX-4` | FE, DES | The product is the workspace; reps must see it early | Five reps clear a synthetic 30-thread backlog in usability testing |
| 10 | Event dictionary, instrumentation, and the baseline dashboard | `ANL-1`, `PLT-2` | DATA | The baseline must be measured before anyone touches the tool | Baseline metrics flowing and accepted by PM and the pilot GMs |

Ticket 6 has a hard dependency on the primary-source re-verification in [09_OPEN_DECISIONS.md](09_OPEN_DECISIONS.md) item `OD-1`. Do not encode messaging rules from a blog post.
