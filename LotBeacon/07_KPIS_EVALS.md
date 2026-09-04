# 07. KPIs and Evaluation

## 1. The hypothesis, stated so it can fail

> **H1.** A sales rep using LotBeacon handles **4x** the qualified Messenger conversations per shift compared with the same rep working the native Page inbox, **without** degrading appointment set rate, show rate, close rate, gross per unit, customer sentiment, or opt-out rate.

Two failure modes that a naive dashboard would call success:

- **Volume without value.** Four times the conversations, half the appointment rate. Guardrail metrics catch it.
- **Definition gaming.** Counting every "is this available" auto-reply as a handled conversation. The definition below prevents it.

### Operational definitions

| Term | Definition |
|---|---|
| **Handled conversation** | A thread with at least one inbound customer message and at least one rep-approved outbound message in the measurement day, where the outbound message advances the thread (answers a question, asks a qualifying question, offers a slot, or resolves an objection). Auto-acknowledgments do not count |
| **Qualified conversation** | A handled conversation where at least two qualifying slots are filled from the customer's own words |
| **Rep-day** | One rep working a scheduled shift of at least 6 hours, excluding partial or training days |
| **Concurrency ceiling** | The p95 number of simultaneously open, non-dormant threads a rep carries without exceeding the response-time target |

Primary metric: **qualified conversations per rep-day**. Secondary primary: **concurrency ceiling**.

---

## 2. KPI tree

### Business outcomes (the only ones that pay for the product)

| KPI | Definition | Target vs baseline | Owner |
|---|---|---|---|
| Appointments set per rep-day | Confirmed appointments from Messenger threads | >= 2x | PM |
| Show rate | Showed / set | No degradation (non-inferiority margin -3pp) | DS |
| Test drives per rep-day | Completed test drives sourced from Messenger | >= 2x | DS |
| Units sold per rep-month from Messenger | Attributed delivered units | >= 1.5x | PM |
| Gross per unit | Front plus back gross on attributed units | Non-inferior (margin -$150) | Dealer GM |
| Cost per appointment | Fully loaded LotBeacon cost / appointments | Below the dealer's current cost per appointment | Finance |

### Throughput (the 4x claim)

| KPI | Target | Notes |
|---|---|---|
| Qualified conversations per rep-day | 4x baseline | Primary |
| Concurrency ceiling | 4x baseline | Confirms the mechanism, not just the count |
| Median first response time | <= 5 minutes during store hours | The strongest known lead-conversion lever |
| p90 response time | <= 30 minutes during store hours | Catches the long tail |
| Threads reaching dormancy without a reply | Down vs baseline | Fewer dropped leads |
| Rep time per handled conversation | Down >= 60% | The mechanism behind 4x |

### AI quality

| KPI | Target | Source |
|---|---|---|
| Draft acceptance rate (sent with no edit or trivial edit) | >= 60% by week 4 | Approval records |
| Median edit distance on edited drafts | Declining trend | Approval records |
| Grounded-claim escape rate | **0** | Validator plus sampled human review |
| Validator block rate | 3% to 15% (below 3% suggests the validator is asleep, above 15% suggests the generator is over-reaching) | Draft telemetry |
| Intent classification macro F1 | >= 0.85 | Eval harness |
| Slot extraction precision | >= 0.95 on budget, trade, timeline, vehicle interest | Eval harness |
| Next-best-action agreement with expert reps | >= 80% | Labeled scenario set |
| p95 draft latency | <= 8 seconds | Traces |

### Customer experience and safety (guardrails, any breach pauses the pilot)

| KPI | Threshold |
|---|---|
| Opt-out rate per 100 threads | No increase vs baseline |
| Page block or report rate | No increase vs baseline |
| Negative sentiment rate at thread end | No increase vs baseline |
| Escalation response time | 95% within 15 minutes during store hours |
| Complaints mentioning "robot", "bot", or "AI" negatively | Tracked, investigated individually |
| Messaging-policy violations | **0** |
| Review-request policy violations (gating, incentives, sentiment filtering) | **0** |
| Security incidents involving customer data | **0** |

---

## 3. Evaluation framework

### Layer 1: offline evals (every merge)

| Suite | Size | Scoring | Gate |
|---|---|---|---|
| Groundedness | 300 golden conversations | Automated claim-to-ledger matching | 100% of restricted claims grounded |
| Policy compliance | 150 scenarios | Rule checks on window, cadence, restricted lexicon, review policy | 100% pass |
| Helpfulness and next action | 200 scenarios | Rubric-scored by a judge model, calibrated quarterly against human raters | >= baseline, no regression beyond noise |
| Tone and voice | 100 scenarios | Style rubric plus a periodic blind rep preference test | >= baseline |
| Red team (hallucination) | 120 attacks | Block or safe-deflect | 100%, zero escapes |
| Prompt injection and abuse | 100 attacks | No unauthorized tool call, no policy bypass | 100% |
| Memory correctness | 80 multi-session cases | Slot precision, contradiction handling, no cross-customer retrieval | Thresholds above, zero leaks |

Judge-model calibration is itself measured: a 50-item human-rated subset is scored quarterly, and if judge-human agreement falls below the agreed kappa, gates revert to human review until recalibrated.

### Layer 2: shadow mode (2 weeks before the pilot)

Drafts are generated for real threads and never shown to anyone except the eval pipeline. Compare the draft against what the rep actually sent: groundedness, tone match, and whether the draft would have answered the question. Exit criterion: zero grounded-claim escapes across at least 2,000 shadow drafts, and >= 50% of drafts rated "would have sent with minor or no edits" by the review panel.

### Layer 3: live pilot (see doc 08)

### Layer 4: continuous production monitoring

| Signal | Cadence | Action on breach |
|---|---|---|
| Sampled human review, 50 drafts per week | Weekly | Prompt or tool fix, regression case added |
| Validator block-reason distribution | Daily | Investigate any new dominant reason |
| Acceptance rate by prompt version | Per release | Rollback if a regression exceeds the threshold |
| Guardrail KPIs | Daily | Auto-pause the affected store on a hard breach |
| Customer complaint triage | 24h SLA | Root cause filed with a fix or an accepted-risk record |

---

## 4. Experiment design for H1

| Element | Choice |
|---|---|
| Unit of assignment | Rep, matched into pairs on the 4-week baseline of qualified conversations per rep-day, tenure, and lead mix |
| Design | Matched-pair randomization within store, with a stepped-wedge crossover at week 5 so every rep eventually gets the tool and each rep serves as their own control |
| Contamination controls | Treated and control reps do not share threads; lead routing rules frozen for the duration; no other tooling or pay-plan changes during the pilot |
| Pre-period | 4 weeks, no exposure |
| Treatment period | 6 weeks, plus a 6-week crossover |
| Primary analysis | Difference-in-differences on qualified conversations per rep-day, with rep-level fixed effects and store-week controls |
| Secondary analysis | Non-inferiority tests on every guardrail KPI |
| Power | Computed from the DISC-1 baseline variance before the pilot starts. If the pilot cannot detect a 2x effect at 80% power, add stores rather than pretend |
| Pre-registration | Analysis plan committed to the repo, with a timestamp, before the first treated conversation |
| Stopping rules | Any guardrail hard breach pauses the affected store. A grounded-claim escape pauses the pilot globally until root cause is fixed |

**Honest reporting rule.** The pilot report states the measured multiple with its confidence interval, whatever that number turns out to be. "2.4x with a stable show rate" is a good result and gets reported as 2.4x.

---

## 5. Counter-metrics we will not ignore

| Risk | Metric | Why it matters |
|---|---|---|
| Rubber-stamping | Blind-send rate (sent under 3 seconds with no edit) | High volume with no reading is how a hallucination reaches a customer |
| Quality theater | Acceptance rate rising while show rate falls | Reps sending easy drafts instead of hard truths |
| Lead cherry-picking | Distribution of conversations per rep by lead quality | Volume gains from skipping hard leads are not real gains |
| Burnout displacement | Rep-reported workload survey, weekly | If reps carry 4x threads and hate it, the product failed |
| Attribution inflation | Reconciliation against the dealer's own source reporting | Overclaiming sales ends the relationship |
