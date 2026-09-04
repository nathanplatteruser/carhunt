# 03. Architecture

## 1. System topology

```
Facebook Page (Messenger)
        |  webhooks (signed)                    ^ Send API (window-checked)
        v                                       |
+-------------------+        +--------------------------+
| ingest-gateway    |  --->  | send-service             |
| verify, dedupe,   |        | window state, suppression|
| enqueue           |        | audit, retries           |
+-------------------+        +--------------------------+
        |                                ^
        v                                |
+---------------------------------------------------------------+
| event bus (per-thread ordered, transactional outbox)           |
+---------------------------------------------------------------+
   |            |               |                |            |
   v            v               v                v            v
+--------+  +---------+  +-------------+  +-------------+  +---------+
|conv-svc|  |identity |  |memory-svc   |  |orchestrator |  |analytics|
|threads |  |resolver |  |slots,summary|  |agent runtime|  |pipeline |
|messages|  |         |  |retrieval    |  |             |  |         |
+--------+  +---------+  +-------------+  +-------------+  +---------+
                                              |      |
                                              v      v
                                   +-------------+  +------------------+
                                   | tool layer  |  | model gateway    |
                                   | grounding   |  | routing, failover|
                                   +-------------+  +------------------+
                                          |
        +---------------+-----------------+------------------+
        v               v                 v                  v
  inventory-svc    crm-connector    calendar-connector   policy-store
  (DMS feed)       (CRM/DMS)        (scheduling)         (store rules)

                        +-------------------------+
                        | workspace-api + web/mobile UI |
                        +-------------------------+
```

### Service responsibilities

| Service | Owns | Never does |
|---|---|---|
| `ingest-gateway` | Signature verification, idempotency, raw event archive, enqueue | Business logic, model calls |
| `conversation-service` | Threads, messages, participants, thread state | External sends |
| `identity-resolver` | Scoped ID to person, CRM contact matching, merge and split | Automatic merges below the confidence threshold |
| `memory-service` | Slots with provenance, rolling summaries, retrieval index, contradiction detection | Storing a fact without a source |
| `orchestrator` | The deterministic agent step machine, tool plans, traces | Free-form loops, direct network calls to vendors |
| `tool layer` | Typed, contract-tested tools over authoritative systems | Returning inferred or model-generated values |
| `model-gateway` | Provider routing, timeouts, cost accounting, failover, redaction | Business rules |
| `send-service` | Window and consent evaluation, delivery, retries, audit | Sending anything without an approval record in v1 |
| `workspace-api` | Rep-facing reads and actions, RBAC | Bypassing send-service |
| `analytics-pipeline` | Event dictionary, warehouse models, dashboards | Reading OLTP directly in production hours |

---

## 2. Data model (core entities)

| Entity | Key fields | Notes |
|---|---|---|
| `tenant` | id, dealer group, plan, config | Isolation boundary |
| `rooftop` | id, tenant_id, timezone, hours, policies, page_id | Store-level config |
| `rep` | id, rooftop_id, role, tone_profile, availability | RBAC subject |
| `person` | id, rooftop_id, scoped_messaging_id, display_name, locale | One per scoped ID per Page. No cross-Page linkage without consent |
| `crm_contact_link` | person_id, crm_id, match_method, confidence, confirmed_by | Ambiguous matches require rep confirmation |
| `thread` | id, person_id, rep_id, state, priority_score, window_expires_at, autonomy_mode | `autonomy_mode` in {draft_only, human_only, assisted_auto} |
| `message` | id, thread_id, direction, channel, body, media[], platform_message_id, sent_by, approval_id | Immutable |
| `profile_slot` | person_id, key, value, type, confidence, source_message_id, source_span, valid_from, stale_at | Provenance is mandatory |
| `commitment` | id, thread_id, text, owner_rep_id, due_at, status, source_message_id | Drives reminders |
| `vehicle` | stock_no, vin, year, make, model, trim, mileage, price, status, title_status, photos[], vdp_url, feed_synced_at | Canonical from the feed |
| `vehicle_interest` | person_id, stock_no, rank, reasons[], rejected_reason | Multiple per person |
| `fact_ledger_entry` | id, draft_id, claim_class, value, source_system, source_record_id, retrieved_at, ttl | See doc 04 |
| `draft` | id, thread_id, body, prompt_version, model, fact_ledger_id, validator_verdict, confidence, blocked_reasons[] | One row per generation attempt |
| `approval` | id, draft_id, rep_id, action, edited_body, edit_distance, decided_at | Required before send in v1 |
| `appointment` | id, thread_id, stock_no, start, type, status, external_id | Two-phase commit |
| `deal_outcome` | person_id, status, delivered_at, unwound_at, source | Drives cadence stops and review eligibility |
| `consent` | person_id, channel, scope, granted_at, evidence, source | Append-only |
| `suppression` | person_id, channel, reason, created_at | Hard block at send time |
| `review_request` | id, person_id, deal_id, platform, sent_at, reminder_sent_at, outcome | Audit for policy compliance |
| `audit_event` | id, actor, action, subject, before, after, at, hash_prev | Append-only, hash-chained |

---

## 3. Identity

1. The inbound event carries a **page-scoped messaging ID**. That is the primary key for a person on that Page. It is not portable across Pages or apps, and the system must not assume it is.
2. **Enrichment** is limited to whatever the platform returns for that scoped ID under the granted permissions.
3. **CRM matching** happens only on identifiers the customer actively supplies in the conversation (phone, email) or that the dealer already has and the rep confirms. Fuzzy name-plus-city matching may **propose** but never **commit** a link.
4. **Merges are reversible.** Every merge stores the evidence and can be undone, because a bad merge shows one customer another customer's history.
5. **Consent and suppression attach to the person, per channel**, and never inherit through a household or a merge in the permissive direction. When two records merge, suppression is the union, consent is the intersection.

---

## 4. Memory architecture

| Tier | Store | Lifetime | Contents | Read path |
|---|---|---|---|---|
| Working | Redis | Current run | Last N turns, active fact ledger, current state | Always |
| Episodic | Postgres | Thread life | Rolling structured summary, stage history, objection log | Always |
| Semantic profile | Postgres | Person life, with staleness | Typed slots with provenance and confidence | Always |
| Commitments | Postgres | Until closed | Promises with owner and due date | Always |
| Archival retrieval | pgvector | Retention window | Message and summary embeddings, scoped by person and tenant | On demand when the model asks about history |
| Grounding cache | Redis with TTL | Seconds to minutes | Recent tool results with freshness age | Per claim class TTL |

**Rules that make memory trustworthy**

- Every slot write carries `source_message_id` plus the extracted span. The API rejects writes without a source.
- Extraction below the confidence threshold produces a **proposed** slot shown to the rep, not a committed one.
- A contradiction between an existing slot and a new extraction creates a `conflict` record. The rep resolves it. The system does not pick a winner silently.
- Slots have `stale_at`. Past that, the UI marks them stale and the generator must re-confirm before relying on them.
- Retrieval queries are always filtered by `tenant_id` and `person_id` at the database level, not in application code.

---

## 5. Customer state machine

```
NEW -> ENGAGED -> QUALIFYING -> VEHICLE_MATCHED -> APPOINTMENT_PROPOSED -> APPOINTMENT_SET
                     |               |                     |                      |
                     v               v                     v                      v
                  OBJECTION <--------+                  NO_SHOW <-------------- SHOWED
                     |                                     |                      |
                     v                                     v                      v
                  NURTURE  ------------------------------> +--------------> SOLD | LOST
                                                                              |
                                                                              v
                                                                          POST_SALE
                                                                              |
                                                                              v
                                                                     REVIEW_REQUESTED -> CLOSED

Orthogonal modes (can apply in any state): HUMAN_ONLY, ESCALATED, DO_NOT_CONTACT, DORMANT
```

| Transition | Trigger | Guard |
|---|---|---|
| `NEW -> ENGAGED` | Inbound message received | None |
| `ENGAGED -> QUALIFYING` | Intent classified as shopping | Not escalated |
| `QUALIFYING -> VEHICLE_MATCHED` | >= 3 core slots filled and inventory match found | Availability confirmed within the freshness SLO |
| `* -> OBJECTION` | Objection classifier fires | None |
| `VEHICLE_MATCHED -> APPOINTMENT_PROPOSED` | Intent score >= threshold or explicit request | Real calendar slots exist |
| `APPOINTMENT_PROPOSED -> APPOINTMENT_SET` | Customer confirms and the calendar write succeeds | Two-phase commit completed |
| `APPOINTMENT_SET -> SHOWED / NO_SHOW` | CRM or DMS record, or explicit rep tap | Never inferred from silence |
| `* -> SOLD / LOST` | Deal record from the DMS, or rep confirmation | Never inferred from conversation text |
| `SOLD -> POST_SALE` | Delivery recorded | Delivered, not just sold |
| `POST_SALE -> REVIEW_REQUESTED` | Eligibility rules in doc 01 stage 11 | No open we-owe, no open complaint, cooldown respected |
| `* -> DO_NOT_CONTACT` | Opt-out phrase, rep action, or CRM flag | Irreversible without an explicit customer request |
| `* -> HUMAN_ONLY` | Rep toggle or escalation trigger | Assistant stops drafting immediately |

---

## 6. Agent runtime

### Triggers

| Trigger | Source | Produces |
|---|---|---|
| Inbound customer message | Messenger webhook | Draft reply run |
| Rep request ("draft a reply", "regenerate", "shorter") | Workspace | Draft run with an instruction override |
| Scheduled follow-up due | Scheduler | Follow-up draft, subject to cadence and window checks |
| Appointment reminder due | Scheduler | Non-promotional confirmation, subject to window rules |
| Inventory event (unit sold, price change) on a watched vehicle | Inventory sync | Proactive draft with a genuine reason |
| Deal outcome recorded | CRM/DMS sync | State change and, when eligible, the review-request draft |

### Run steps (deterministic order, capped)

| # | Step | Failure behavior |
|---|---|---|
| 1 | Load thread state, autonomy mode, suppression, window state | Hard stop if suppressed or `HUMAN_ONLY` |
| 2 | Classify intent, objection, sentiment, urgency; abstain if uncertain | Abstain routes to the rep with no draft claim |
| 3 | Assemble memory context (working, episodic, profile, retrieval) | Continue with what loaded; mark the missing tier in the trace |
| 4 | Plan tool calls from the claim requirements of the intended reply | Empty plan is allowed only for non-factual replies |
| 5 | Execute tools in parallel with per-tool timeouts and write the Fact Ledger | Any required tool failure downgrades the reply to "cannot verify" language |
| 6 | Generate the draft constrained to the ledger | Retry once with a tighter constraint prompt on validator failure |
| 7 | Validate claims against the ledger and the restricted-language lexicon | Fail closed: block, show the reason, escalate if the class requires it |
| 8 | Compute next-best-action and confidence | Low confidence surfaces a banner |
| 9 | Queue for rep approval | Never auto-send in v1 |
| 10 | Emit trace, metrics, and audit records | Telemetry failure never blocks a reply |

Caps: maximum 2 generation attempts, maximum 8 tool calls, maximum 15 seconds wall clock before the workspace shows a partial state with a manual retry.

### Tool catalogue

| Tool | Reads from | Claim classes it authorizes | Notes |
|---|---|---|---|
| `inventory.search` | Inventory service | Vehicle existence, specs present in the feed | Structured filters only |
| `inventory.get` | Inventory service | Price, mileage, VIN, title status, photos, VDP link | Returns `synced_at` |
| `inventory.availability` | DMS plus holds | Availability | Short TTL, returns freshness age |
| `spec.lookup` | Curated spec table | Third row, cargo class, tow rating | Conservative when unmatched |
| `calendar.slots` | Scheduling system | Appointment times | Store hours enforced |
| `calendar.hold` / `calendar.book` | Scheduling system | Appointment confirmation | Two-phase commit |
| `crm.get_contact` / `crm.log_activity` | CRM | Prior history, ownership | Write is idempotent |
| `deal.status` | DMS | Sold, delivered, unwound | Drives cadence stops |
| `policy.lookup` | Policy store | Warranty, as-is status, delivery, hold, test-drive requirements | Store-authored text only |
| `valuation.range` | Valuation vendor | Trade range as an estimate | Requires human sign-off before sending |
| `finance.disclosure` | Approved copy library | Financing language and the secure application link | Never predicts approval |
| `history.summary` | Vehicle history vendor | Accident, title, owner count | Subject to license terms |
| `recall.lookup` | Public recall data | Open recall by VIN | Read-only |
| `review.link` | Review platform config | The review destination URL | No incentive language |

Tools are **allowlisted per intent**. Customer text can never expand the allowlist. See `AI-10` in doc 02.

### Escalation triggers

| Trigger | Action | SLA |
|---|---|---|
| Legal threat, attorney mention, regulator mention | Human-only, notify manager | Immediate |
| Complaint or anger above the sentiment threshold | Human-only, notify manager | 15 minutes during store hours |
| Discrimination-adjacent, credit-decision, or protected-class topics | Human-only, no draft | Immediate |
| Distress or safety language | Human-only, no draft, manager notified | Immediate |
| Negotiation on price, payment, or trade value | Draft blocked on numbers, rep decision required | Next rep action |
| Minor or suspected minor | Human-only | Immediate |
| Validator block twice in a row | Human-only for the turn | Next rep action |
| Integration outage affecting a required claim | Rep-visible banner, degraded draft | Until restored |

### Retries and idempotency

| Operation | Policy |
|---|---|
| Webhook processing | At-least-once with an idempotency key on the platform message ID |
| Model call | 1 retry on timeout, then failover model, then degrade to no draft |
| Tool call | 2 retries with jitter, circuit breaker per vendor |
| Send | Exactly-once per approval record; a duplicate approval never produces a second send |
| CRM write | Idempotency key on the internal message ID |
| Calendar book | Hold, confirm, verify; on verify failure, release and alert |

### Observability and audit

- **Trace**: one span tree per run with the prompt version, model, token counts, latency, tool calls with arguments and results (PII-redacted), validator verdicts, and the final disposition.
- **Metrics**: ingest lag, draft latency p50/p95, tool error rate by vendor, validator block rate by class, acceptance rate, edit distance, send success, window-block rate.
- **Logs**: structured, PII-masked per the classification in `SEC-2`.
- **Audit**: append-only and hash-chained. Answers, for any message, who approved it, which draft it came from, which facts backed it, and which prompt version wrote it. Retained per the schedule in doc 06.

### Fallback ladder

| Level | Condition | Behavior |
|---|---|---|
| 0 | Everything healthy | Grounded draft, full context |
| 1 | Non-critical tool down | Draft without that claim class, banner shown |
| 2 | Required tool down (availability, calendar) | Draft says the rep is confirming; no factual assertion |
| 3 | Model gateway down | No draft. Thread still ranked in the inbox with the summary and next-best-action from the last known state |
| 4 | Memory service down | Raw transcript view only, drafting disabled |
| 5 | Kill switch active | Read-only workspace, reps work in the native Page inbox, all events still archived |
