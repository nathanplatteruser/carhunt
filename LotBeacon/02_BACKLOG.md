# 02. Backlog

Ticket-ready. Every ID maps to one Jira/Linear issue. Columns are fixed: **P** priority, **Owner** team, **Deps** blocking IDs, **Deliverable**, **Acceptance criteria**, **Key failure risks**, **DoD** measurable definition of done.

Teams: `PM` product, `PLAT` platform engineering, `AAI` applied AI, `INT` integrations engineering, `FE` frontend, `DATA` data engineering, `SEC` security engineering, `LEG` legal and compliance, `DES` design, `QA` quality, `DS` dealer success.

Priority rubric: **P0** blocks pilot, **P1** blocks general availability, **P2** post-GA improvement.

---

## 1. Discovery (`DISC`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| DISC-1 | Rep shadowing study, 3 stores, 5 reps, 2 shifts each | P0 | PM, DES | - | Time-and-motion report with the current conversations-per-rep-per-day baseline and the handling-time distribution | Baseline median and p90 handling time per conversation, current concurrent-thread ceiling, and the top 10 message archetypes are quantified from observed data | Volunteer bias toward high performers; stores with atypical lead mix | Report reviewed by 2 store GMs, baseline numbers loaded into the analytics warehouse as the pre-period benchmark |
| DISC-2 | Message corpus analysis, 90 days of historical Messenger threads (consented, de-identified) | P0 | PM, DATA | SEC-2 | Intent taxonomy with observed frequency, objection taxonomy, and a labeled sample of 1,000 messages | Taxonomy covers >=95% of sampled messages with an "other" bucket under 5%; inter-annotator agreement kappa >= 0.75 | Export limits on historical data; PII in the corpus | Taxonomy versioned in the repo, labeled sample stored in the eval bucket with access logging |
| DISC-3 | Systems inventory per pilot store (DMS, CRM, inventory feed, calendar, valuation tool, vehicle history, payment calculator) | P0 | PM, INT | - | Integration matrix listing vendor, API availability, auth model, rate limits, data freshness, contract owner | Every factual claim class in doc 04 maps to a named authoritative system or is explicitly marked unsupported | Vendor API access requires dealer-level contract changes | Matrix signed by each pilot store's GM and the vendor contacts identified |
| DISC-4 | Define "handled conversation" and the 4x hypothesis operationally | P0 | PM, DATA | DISC-1 | Written metric definition and the counting rules | Definition survives adversarial review (cannot be gamed by splitting or auto-closing threads); implemented as SQL against the event log | Metric drift between pilot and control | Definition merged, dashboards computing it on the pre-period baseline |
| DISC-5 | Competitive and vendor teardown of incumbent dealer chat tools | P2 | PM | - | Positioning brief with the specific gaps LotBeacon targets | Names 5 incumbents with their messaging-window handling and grounding approach | Feature-chasing | Brief reviewed, roadmap deltas logged in doc 09 |

---

## 2. Meta integration (`META`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| META-1 | Meta app, business verification, Page onboarding OAuth flow | P0 | INT, LEG | DISC-3 | Tech Provider app with the Page-scoped install flow and token vault | A store admin can connect a Page in under 5 minutes; tokens stored encrypted with rotation; disconnect revokes cleanly | Business verification delays measured in weeks; wrong app type chosen | Two pilot Pages connected in staging and production, runbook written |
| META-2 | Webhook ingestion endpoint | P0 | PLAT | META-1 | Signed webhook receiver for message, postback, read, reaction, and echo events with idempotent enqueue | Signature verification enforced; duplicate delivery produces one stored message; p99 ack under 500ms; 24h replay from the raw event archive | Silent event loss during deploys; unverified payloads accepted | Load test at 20x pilot peak passes, zero duplicates in a 100k-event replay |
| META-3 | Send layer with messaging-window state machine | P0 | PLAT, LEG | META-2, CMP-1 | Send service that computes the current allowed message type per thread and refuses non-compliant sends | Every send is pre-checked against window state and consent; refusals produce an explainable UI reason; all sends recorded in the audit log | Policy violation leading to app restriction; a rep blaming the tool for a blocked send | 100% of synthetic window scenarios in the compliance test suite pass, including window expiry mid-draft |
| META-4 | Message-tag and template migration path | P0 | INT, LEG | META-3 | Adapter for permitted out-of-window message types with a template registry and approval status | Templates registered and approved before pilot; the code path fails closed when a template is unapproved or unavailable in the region | Platform deprecation timelines shifting under us | Approved template set live, deprecation watch item in doc 09 with a named owner |
| META-5 | Attachments, media, and listing-card parsing | P1 | PLAT, AAI | META-2 | Handlers for image, video, file, location, and Marketplace or ad referral payloads with media stored server-side | Vehicle referenced by a shared listing resolves to a stock number in >=90% of pilot cases; unsupported media degrade to a rep-visible note | Media URL expiry; unparseable card formats | Fixture suite of 50 real payload types green in CI |
| META-6 | Handover protocol and Page inbox coexistence | P1 | PLAT | META-2 | Thread control handling so a rep replying in the native Page inbox does not collide with LotBeacon | Native-inbox replies appear in LotBeacon within 60 seconds; no duplicate outbound message in any tested race | Two systems answering the same customer | Race-condition test suite green; store trained on the coexistence model |
| META-7 | Rate limiting, backoff, and error taxonomy | P1 | PLAT | META-3 | Central Meta client with per-Page quotas, exponential backoff, circuit breaker, and mapped error codes | Every documented error code has a defined behavior (retry, escalate, block, alert); no unbounded retry loops | Throttling during evening peak; retry storms | Chaos test with injected 429/500 responses keeps send success >=99% with no duplicate sends |
| META-8 | App review submission package | P0 | INT, LEG, PM | META-3 | Screencast, use-case justification, and permission scope rationale | Submission accepted; permissions granted for the exact scopes the product uses and no more | Rejection cycles adding weeks | Permissions live in production, scope list documented |

---

## 3. System architecture (`ARCH`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| ARCH-1 | Service topology and repo scaffold | P0 | PLAT | - | Monorepo with ingest gateway, conversation service, memory service, grounding service, orchestrator, workspace API, integrations service, analytics pipeline | Local `make dev` boots the full stack with seeded data in under 5 minutes | Premature microservice sprawl | New engineer runs the stack end to end on day one, documented in the README |
| ARCH-2 | Multi-tenant isolation model | P0 | PLAT, SEC | ARCH-1 | Tenant = dealer group, sub-tenant = rooftop, with row-level security and tenant-scoped keys | No query path can read across tenants; verified by an automated cross-tenant test suite | Cross-tenant leak, the single worst incident class | Cross-tenant test suite in CI; a deliberate leak attempt fails in staging |
| ARCH-3 | Event bus and outbox pattern | P0 | PLAT | ARCH-1 | Durable event log with transactional outbox for every state change | At-least-once delivery with idempotent consumers; ordered per thread; replay reconstructs state | Lost commitments and duplicate customer messages | Replay of a full day rebuilds identical thread state in staging |
| ARCH-4 | Configuration and feature-flag service | P0 | PLAT | ARCH-1 | Per-tenant config for autonomy level, cadence limits, tone, hours, escalation routing, enabled tools | Config change takes effect within 60 seconds without deploy; every change audited | Flag drift between stores; unsafe default on | Defaults documented; a config change is demonstrated live with an audit record |
| ARCH-5 | Environments and data separation | P0 | PLAT, SEC | ARCH-2 | Dev, staging with synthetic data, and production with no production PII in lower environments | Staging seeded only from synthetic generators; a scan proves no real customer data below production | Engineers debugging with live PII | Automated PII scan gate on lower environments passing weekly |

---

## 4. Customer and thread identity (`IDN`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| IDN-1 | Page-scoped ID handling and person record | P0 | PLAT | META-2 | `person` entity keyed by scoped messaging ID per Page, with the display profile fields the platform actually returns | One person per scoped ID per Page; no assumption that the same human on two Pages is linkable without consent | Wrongly merging two customers, which leaks one customer's data to another | Merge and split operations covered by tests, including the un-merge path |
| IDN-2 | Deterministic CRM matching | P0 | INT | IDN-1, CRM-1 | Matcher on phone and email captured in-conversation with explicit customer provision | Match precision >= 0.99 on the labeled set; ambiguous matches go to a rep confirmation step rather than auto-merging | False merges creating cross-customer disclosure | Precision measured on 500 labeled pairs, ambiguous queue live |
| IDN-3 | Household and duplicate handling | P2 | DATA | IDN-2 | Household grouping with per-person consent kept separate | Consent and opt-out never inherit across household members | Messaging an opted-out spouse | Test proves suppression is per person |
| IDN-4 | Thread lifecycle and reassignment | P1 | PLAT | IDN-1 | Thread ownership model with reassignment, vacation coverage, and manager takeover | Ownership change preserves memory and audit trail; the customer sees continuity, not a restart | Orphaned threads when a rep leaves | Rep offboarding runbook executed in staging with zero orphaned threads |

---

## 5. Data model (`DATA`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| DATA-1 | Core schema (tenant, rooftop, rep, person, thread, message, vehicle, appointment, deal, consent, audit) | P0 | PLAT, DATA | ARCH-1 | Migrations plus an entity-relationship document | Every entity in doc 03 exists with constraints; no nullable foreign keys on required relations | Schema churn late in the build | Migrations applied in all environments, ERD merged |
| DATA-2 | Customer profile slot store with provenance | P0 | PLAT, AAI | DATA-1 | `profile_slot` table storing value, confidence, source message ID, extracted span, and updated timestamp | Every slot value traces to a message or an integration record; unsourced writes rejected at the API | Memory that cannot be defended to a customer or a regulator | 100% of slots in a sampled thread trace to a source; enforced by a database constraint |
| DATA-3 | Commitments ledger | P0 | PLAT | DATA-1 | `commitment` entity with promise text, owner, due time, status, source message | Every commitment surfaces in the rep UI until closed; overdue commitments alert | Broken promises, the top trust killer in retail auto | Overdue alert fires in a staged scenario; ledger visible in the workspace |
| DATA-4 | Consent and suppression store | P0 | PLAT, LEG | DATA-1, CMP-1 | `consent` and `suppression` tables with channel, scope, timestamp, evidence, and source | Send layer queries suppression on every outbound; suppression is append-only and never soft-deleted | Messaging someone who opted out | Send blocked in an automated test for every suppression type |
| DATA-5 | Retention and deletion jobs | P1 | DATA, LEG | DATA-1, CMP-4 | Scheduled jobs implementing the retention schedule, including hard delete and derived-data purge | Deletion removes source records, embeddings, caches, and warehouse rows within the SLO; a report proves completion | Orphaned embeddings and warehouse copies surviving a deletion request | End-to-end deletion drill verified across all stores including the vector index |
| DATA-6 | Analytics warehouse modeling | P1 | DATA | ARCH-3 | Star schema for conversations, drafts, sends, appointments, and outcomes | Metrics in doc 07 computable without touching production OLTP | Metric definitions diverging between dashboards | dbt models tested, freshness checks green |

---

## 6. Conversation memory (`MEM`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| MEM-1 | Working memory assembly | P0 | AAI | DATA-1 | Context builder producing the last N turns plus a token budget policy | Deterministic given the same inputs; budget never exceeded; truncation never silently drops the most recent customer message | Context overflow dropping the actual question | Golden-context tests pass; builder output snapshot-tested |
| MEM-2 | Rolling thread summary | P0 | AAI | MEM-1 | Incremental summarizer with a stable schema (facts, open questions, objections, commitments, sentiment, next action) | Summary regenerates deterministically enough to pass a stability test; contains no claim absent from the thread or ledger | Summary drift inventing customer preferences | Hallucination rate on the summary eval set below the doc 07 threshold |
| MEM-3 | Structured slot extraction | P0 | AAI | DATA-2 | Extractor writing typed slots with confidence and provenance | Precision >= 0.95 on the labeled set for budget, trade, timeline, and vehicle interest; low-confidence extractions are proposed, not committed | Confidently wrong budget or trade details steering the whole deal | Precision and recall reported per slot in the eval report |
| MEM-4 | Contradiction detection and resolution | P1 | AAI | MEM-3 | Detector flagging conflicting slot values with both sources shown to the rep | Conflicts surface in the workspace rather than being silently overwritten; rep resolution is one click and audited | Silent overwrite losing the truth | Conflict scenario suite green; UI reviewed with reps |
| MEM-5 | Long-term retrieval across thread history | P1 | AAI, DATA | DATA-1 | Embedding index over messages and summaries scoped strictly per person and tenant | Retrieval never returns another customer's content in an automated adversarial test; recall@5 measured on a labeled question set | Cross-customer retrieval leak | Adversarial retrieval test in CI with zero leaks |
| MEM-6 | Memory decay and relevance policy | P2 | AAI | MEM-5 | Recency and relevance weighting so a 9-month-old budget does not override today's | Stale slots are marked stale in the UI past the configured age; the model prefers fresher provenance | Acting on dead information | Policy documented and reflected in the workspace profile card |
| MEM-7 | Customer-facing memory transparency | P2 | PM, FE | MEM-3 | Rep-visible "what we remember and why" panel plus an export path for data requests | A rep can explain any remembered fact with its source in under 10 seconds | Uncomfortable surprises about what is stored | Usability test with 5 reps passes |

---

## 7. Vehicle inventory grounding (`INV`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| INV-1 | Inventory ingestion and normalization | P0 | INT, DATA | DISC-3 | Feed connector normalizing to a canonical vehicle record with a freshness timestamp | Full sync plus incremental updates; freshness p95 under the agreed SLO; sold units flagged, not deleted | Stale feed asserting a sold car is available | Freshness monitor alerting; sold-unit test case verified against the DMS |
| INV-2 | Availability and hold semantics | P0 | INT | INV-1 | Availability resolver combining feed status, deal status, and rep-placed holds | Availability answers carry a freshness age; stale answers are downgraded to "confirming" language | Selling a car twice | Availability contract test against the DMS passes for all status transitions |
| INV-3 | Structured vehicle search tool | P0 | AAI, INT | INV-1 | Filterable search (body, seats, drivetrain, price, mileage, payment-eligible, distance, title status) returning citable records | Every returned attribute is a stored field; no derived or inferred specs in the tool response | Model inventing a trim feature | Tool contract test asserts response fields map one to one to the schema |
| INV-4 | Curated spec table for third row, cargo, tow | P1 | DATA, PM | INV-1 | Ordered match-pattern table mapping model and trim to guaranteed, trim-dependent, or unavailable capability | Every recommendation involving seating or towing cites the table or declines to answer | Confidently promising a third row that is not there | Table covers 100% of pilot inventory models; unmatched units answer conservatively |
| INV-5 | Media and VDP link resolution | P1 | INT | INV-1 | Photo set and canonical vehicle detail page URL per stock number | Links resolve to a live page for 100% of available units; broken links block the draft | Sending a customer a dead link | Link checker running on every sync |
| INV-6 | Cross-rooftop inventory rules | P2 | PM, INT | INV-1, ARCH-2 | Configurable policy for whether a rooftop can quote a sister store's unit | Policy respected in search results; disclosure text attached when the unit is at another location | Promising a car the customer cannot drive today | Policy toggle tested per rooftop |

---

## 8. AI orchestration (`AI`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| AI-1 | Orchestrator runtime | P0 | AAI, PLAT | ARCH-3, MEM-1 | Deterministic step machine: classify, retrieve, plan, call tools, generate, validate, queue for approval | Every run emits a full trace; identical inputs plus a fixed seed reproduce the same tool plan | Free-running agent loops burning cost and time | Trace viewer shows every step of a production run; loop cap enforced |
| AI-2 | Intent and objection classification | P0 | AAI | DISC-2 | Classifier over the taxonomy with calibrated confidence and an abstain class | Macro F1 >= 0.85 on the held-out set; abstain routes to the rep with no draft claim | Misrouted intent producing an off-topic reply | Confusion matrix published; abstain path tested |
| AI-3 | Model gateway and provider abstraction | P0 | PLAT, AAI | ARCH-1 | Provider-agnostic gateway with per-tenant model routing, timeouts, cost accounting, and a fallback model | Failover to the secondary model within the latency budget; cost attributed per tenant and per draft | Single-vendor outage stopping the product | Failover drill passes with drafts still produced |
| AI-4 | Prompt and policy versioning | P0 | AAI | ARCH-4 | Versioned prompt registry with changelog, eval score per version, and rollback | No prompt reaches production without an eval run attached; rollback in under 5 minutes | Silent prompt edits degrading quality | Rollback drill executed and timed |
| AI-5 | Reply generation with tone profiles | P0 | AAI, DES | MEM-2, INV-3 | Generator producing a rep-voice draft constrained to the fact ledger, with per-rep tone calibration | Drafts pass the style rubric; length within channel norms; no emoji or exclamation storms unless the rep profile allows | Robotic or over-eager copy that customers can smell | Blind rep preference test beats the current template baseline |
| AI-6 | Claim validator (fail-closed) | P0 | AAI, QA | GRD suite in doc 04 | Post-generation validator extracting factual claims and matching them to fact-ledger entries | Any unmatched claim in a restricted class blocks the draft and shows the rep why; zero unmatched claims escape in the red-team suite | The single largest product risk: a confident wrong number | Red-team suite passes at 100% block rate on injected hallucinations |
| AI-7 | Next-best-action policy | P1 | AAI, PM | AI-2, MEM-2 | Ranked action recommendation (ask, recommend, book, escalate, wait, close) with a reason string | Recommendation matches expert rep judgment on >= 80% of the labeled scenario set | Pushing for a booking too early and burning the lead | Agreement measured against a 200-scenario expert-labeled set |
| AI-8 | Follow-up scheduler | P1 | AAI, PLAT | META-3, DATA-3 | Rule engine generating due follow-ups with reason codes, respecting caps and windows | No follow-up generated that violates cadence caps, quiet hours, or suppression | Nagging customers into blocking the Page | Simulation over 30 days of synthetic threads produces zero cap violations |
| AI-9 | Cost and latency budget | P1 | AAI, PLAT | AI-3 | Per-draft budget with caching, prompt compression, and small-model routing for classification | p95 draft latency under 8 seconds from inbound message; cost per draft under the target | Unit economics that never work at scale | Budget dashboard live with alerting |
| AI-10 | Prompt-injection and adversarial-input defense | P0 | AAI, SEC | AI-1 | Untrusted-content isolation, tool-call allowlisting, and instruction-hierarchy enforcement | Customer text cannot trigger tool calls outside the allowlist or alter policy; injection suite blocked at 100% | A customer talking the assistant into a discount or into leaking data | Injection corpus of 100 attacks fully blocked, re-run in CI |

---

## 9. Agent workflows (`WF`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| WF-1 | Customer state machine | P0 | PLAT, PM | DATA-1 | Explicit state machine with allowed transitions and the events that cause them | Illegal transitions rejected and logged; state history queryable | Ambiguous state producing the wrong cadence | Transition table tested exhaustively |
| WF-2 | First-response workflow | P0 | AAI | AI-1, INV-2 | Playbook for inquiry, availability check, and a qualifying question | Median draft ready under 60 seconds of inbound; availability always grounded | Slow first response, the biggest lead-loss factor | Timing measured on pilot traffic |
| WF-3 | Qualification workflow | P0 | AAI, PM | MEM-3 | Slot-filling playbook with a maximum of two questions per message and no repeats | Never re-asks a filled slot; drops to the rep after three unanswered attempts | Interrogation feel driving abandonment | Repeat-question rate measured at zero on the eval set |
| WF-4 | Appointment booking workflow | P0 | AAI, INT | CRM-3 | Slot offer, hold, confirm, write, and confirmation scheduling | Two-phase commit with rollback; no slot offered outside store hours or availability | Double bookings and no-shows caused by phantom slots | Booking integration test green against the real calendar sandbox |
| WF-5 | Objection playbooks | P1 | AAI, PM | AI-2, GRD | Per-objection response patterns with hard limits on price, payment, and trade language | Restricted classes always route to a human decision; no discount language generated | Unauthorized negotiation | Playbook review signed by a store GM and legal |
| WF-6 | Escalation and human-approval gates | P0 | PLAT, PM | ARCH-4 | Escalation triggers (legal threat, complaint, distress, discrimination-adjacent topics, minors, negotiation, unresolved conflict, low confidence) with routing and SLA | 100% of trigger phrases in the test corpus escalate; escalations page the right person | An angry customer stuck in an automated loop | Escalation drill completed with a measured response time |
| WF-7 | Review-request workflow | P0 | AAI, LEG | CMP-3, CRM-2 | Eligibility rules, neutral non-incentivized ask, one reminder cap, and full audit | No filtering by predicted sentiment; no incentive language; identical ask for all eligible customers | Review gating, which is both a policy violation and a legal exposure | Compliance test suite for review requests passes; wording approved by legal |
| WF-8 | Dormancy, re-engagement, and closure | P2 | AAI, PM | AI-8 | Rules for going dormant and the conditions for a genuine reason to reopen | Re-engagement requires a new fact (price change, matching arrival), never a bare check-in | Spam behavior damaging the Page | Simulation shows no reason-free reopens |
| WF-9 | Retry, timeout, and degraded-mode behavior | P0 | PLAT, AAI | ARCH-3 | Defined behavior when a tool, model, or integration fails | Degrades to a rep-visible "cannot verify" state; never guesses; never silently drops a customer message | Silent failure leaving a customer unanswered | Fault-injection suite covering every tool passes |

---

## 10. Rep workspace UX (`UX`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| UX-1 | Prioritized inbox | P0 | FE, DES | AI-7 | Inbox with a transparent priority score, urgency bands, and filters | A rep can explain why a thread is at the top; sort is stable and does not jump under the cursor | Reps abandoning it for the native Page inbox | Task test: 5 reps clear a 30-thread backlog faster than in the native inbox |
| UX-2 | Conversation view with summary-first layout | P0 | FE, DES | MEM-2 | Three-line recap, full transcript on demand, and inline fact citations | A rep resumes a 3-week-old thread in under 15 seconds in usability testing | Wall of text nobody reads | Usability benchmark met with 5 reps |
| UX-3 | Customer profile and vehicle context panels | P0 | FE | MEM-3, INV-3 | Slot list with provenance tooltips, vehicle cards with live availability and freshness age | Every displayed fact shows its source on hover; stale data is visibly stale | Reps trusting an old number | Review with reps confirms no unsourced facts on screen |
| UX-4 | Editable draft with risk and confidence banners | P0 | FE, DES | AI-6 | Draft editor showing blocked claims, low-confidence flags, and required human decisions | Blocked drafts cannot be sent until the rep supplies or confirms the fact; the banner explains the specific reason | Warning fatigue leading to blind sending | Banner comprehension test with reps; blocked-send path verified |
| UX-5 | One-click actions: send, edit and send, regenerate, escalate, human-only | P0 | FE | META-3 | Action bar with keyboard shortcuts and an undo window | Send round trip under 2 seconds p95; human-only mode stops drafting immediately | Accidental sends | Undo and human-only verified in a live staging thread |
| UX-6 | Commitments and reminders | P1 | FE | DATA-3 | Due and overdue commitment list with snooze and complete | Overdue items are impossible to miss in the daily view | Forgotten promises | Reps confirm in the pilot survey that no promise was lost |
| UX-7 | Test-drive CTA and booking widget | P1 | FE, INT | WF-4 | Inline slot picker producing a booked appointment without leaving the thread | Booking completes in under 20 seconds from the thread view | Reps booking in a second system and desynchronizing | Time-on-task measured under the target |
| UX-8 | Mobile-first responsive workspace | P1 | FE, DES | UX-1 | Phone layout for triage on the floor | Core loop (read recap, approve, send) works one-handed on a phone | Reps are never at a desk | Mobile task test passes with 5 reps |
| UX-9 | Manager console | P2 | FE, PM | ANL-2 | Queue health, escalations, edit-rate outliers, review-request compliance | A manager can identify the three threads most at risk in under a minute | Coaching blind spots | Console reviewed with two GMs |
| UX-10 | Onboarding and voice calibration | P2 | DES, AAI | AI-5 | Rep setup capturing tone samples and preferences | New rep produces an acceptable first draft within 10 minutes of setup | Generic voice that reps rewrite every time | Median edit distance below the doc 07 target after calibration |

---

## 11. CRM and dealer systems (`CRM`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| CRM-1 | CRM connector (read: contacts, leads, deals) | P0 | INT | DISC-3 | Connector with mapped fields and a sync scheduler | Contact and lead reads reconcile with the CRM UI on a 100-record audit | Vendor API limits or a closed API forcing manual workflows | Reconciliation report shows zero mismatches |
| CRM-2 | CRM write-back (activities, notes, outcomes) | P0 | INT | CRM-1 | Idempotent activity logging for every sent message, appointment, and outcome | No duplicate activities on retry; every LotBeacon send appears in the CRM timeline within the sync SLO | Duplicate or missing activity breaking dealer reporting and pay plans | 24h soak shows zero duplicates and zero drops |
| CRM-3 | Calendar and appointment integration | P0 | INT | CRM-1 | Availability read and appointment write against the store's scheduling system | Slots offered exist and are bookable; cancellations propagate both ways | Phantom slots destroying customer trust | Bidirectional sync test passes including cancel and reschedule |
| CRM-4 | Deal and delivery outcome sync | P1 | INT, DATA | CRM-1 | Sold, delivered, and unwound status from the DMS | Review eligibility and cadence stops are driven by a system record, not by conversation text | Asking for a review on a deal that fell apart | Outcome-driven stop verified in an end-to-end test |
| CRM-5 | Vehicle history and valuation tool connectors | P1 | INT, LEG | DISC-3 | Read-only connectors with license-compliant display and caching rules | Only licensed fields are surfaced; caching honors the vendor contract | License violation from redistributing report content | Legal sign-off recorded per vendor |
| CRM-6 | Integration failure surfacing | P1 | INT, FE | CRM-1 | Health indicators in the workspace when a system is down | A rep sees "cannot verify availability" rather than a confident wrong answer | Silent degradation | Fault-injection test shows the correct banner in every case |

---

## 12. Analytics (`ANL`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| ANL-1 | Event instrumentation spec | P0 | DATA, PM | ARCH-3 | Canonical event dictionary covering every state change, draft, edit, send, and outcome | Every KPI in doc 07 is computable from events with no manual joins | Unmeasurable pilot | Dictionary merged, events flowing, coverage test green |
| ANL-2 | Pilot dashboard | P0 | DATA | ANL-1, DATA-6 | Dashboard for the primary and guardrail metrics, sliced by rep, store, and cohort | Refreshes daily; discrepancies against the CRM under 2% | Arguing about numbers instead of results | Signed off by PM and the pilot GMs |
| ANL-3 | Draft quality telemetry | P1 | DATA, AAI | UX-4 | Acceptance rate, edit distance, regeneration rate, and block reasons per prompt version | Quality regressions detectable within 24 hours of a prompt change | Blind model changes | Alert fires on a synthetic regression |
| ANL-4 | Attribution from first message to delivered unit | P1 | DATA, INT | CRM-4 | Joined funnel from ad referral through Messenger to a delivered deal | Attribution reconciles with the CRM's own source reporting within tolerance | Overclaiming credit for sales | Reconciliation documented and accepted by the dealer |
| ANL-5 | Cost per conversation and per appointment | P2 | DATA | AI-9 | Unit economics reporting per tenant | Finance can price the product from this report | Negative gross margin discovered late | Report reviewed with finance |

---

## 13. Security (`SEC`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| SEC-1 | Threat model and security architecture review | P0 | SEC | ARCH-1 | STRIDE-style threat model covering the agent, tools, and integrations | Every high-severity threat has a mitigation or an accepted-risk record | Unknown attack surface in an AI-plus-integrations product | Threat model reviewed and signed; issues tracked |
| SEC-2 | Data classification and PII handling | P0 | SEC, LEG | DATA-1 | Classification of every field with masking rules for logs, traces, and prompts | No PII in application logs or third-party traces; verified by an automated scanner | PII leaking into vendor logs | Scanner in CI with zero findings on a 7-day production sample |
| SEC-3 | Encryption, key management, secrets | P0 | SEC, PLAT | ARCH-1 | Encryption in transit and at rest, managed keys, rotation, and no secrets in code | Secret scanning blocks commits; keys rotate on schedule | Leaked Page tokens giving attackers a dealer's inbox | Rotation drill executed; scanner enforced in CI |
| SEC-4 | Authentication, authorization, and roles | P0 | SEC, PLAT | ARCH-2 | SSO, MFA for admin roles, and RBAC (rep, manager, admin, support) with least privilege | A rep cannot read another store's threads; support access is time-boxed and logged | Overbroad internal access | Access matrix tested; support access requires an approved break-glass record |
| SEC-5 | Audit logging (append-only) | P0 | SEC, PLAT | ARCH-3 | Tamper-evident audit log of every message sent, approval, config change, and data access | Log entries are immutable and hash-chained; queryable per customer for a data request | Cannot prove who said what to a customer | Audit query answers "who sent this and when" for any message in the pilot |
| SEC-6 | Vendor and subprocessor review | P1 | SEC, LEG | AI-3 | Reviewed subprocessor list including model providers, with data-use terms | No provider trains on dealer or customer data; terms documented per vendor | Customer data used for model training | Signed terms filed; subprocessor page published |
| SEC-7 | Incident response plan | P0 | SEC, LEG | SEC-1 | Runbook with severity levels, notification obligations, timelines, and contacts | Tabletop exercise completed; notification timelines are documented and met in the drill | Improvised response during a real breach | Tabletop report filed; on-call rota live |
| SEC-8 | Penetration test and remediation | P1 | SEC | SEC-4 | Third-party test covering the app, API, and agent tool surface | All critical and high findings remediated or formally accepted before GA | Shipping an exploitable multi-tenant system | Retest confirms remediation |

---

## 14. Compliance (`CMP`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| CMP-1 | Messaging-policy compliance engine | P0 | LEG, PLAT | META-3 | Rules engine implementing platform messaging windows, permitted message types, and content restrictions | Every send is evaluated; blocked sends explain the rule; rules are versioned and dated | Platform enforcement action removing messaging access | Compliance test suite green; rules reviewed by counsel |
| CMP-2 | Consent, disclosure, and opt-out | P0 | LEG, PM | DATA-4 | Consent capture, automation disclosure text, and opt-out phrase handling in every supported channel | Opt-out honored within seconds and propagated to CRM within the sync SLO; disclosure text approved | Continuing to message after a stop request | Opt-out end-to-end test passes on every channel |
| CMP-3 | Review-request policy compliance | P0 | LEG, PM | WF-7 | Written policy plus enforcement: no gating, no incentives, no sentiment filtering, no scripted customer wording | Automated check proves review requests are sent to all eligible customers regardless of predicted sentiment | Platform penalties and regulatory exposure for gated or incentivized reviews | Policy published, enforcement test in CI, legal sign-off |
| CMP-4 | Data retention schedule and data-subject requests | P0 | LEG, DATA | DATA-5 | Retention schedule per data class and a request-handling runbook (access, deletion, correction, opt-out of sale or share) | Requests fulfilled within statutory deadlines; proof of deletion generated | Missed statutory deadline | Two live drills completed within the deadline |
| CMP-5 | Dealer-facing DPA, terms, and role allocation | P0 | LEG | SEC-6 | Contract set defining the dealer as controller and LotBeacon as processor, with subprocessors listed | Executed with every pilot store before any production data flows | Processing personal data with no lawful basis or contract | Signed agreements on file for all pilot stores |
| CMP-6 | Advertising and claims review of generated content | P1 | LEG, PM | AI-5 | Restricted-language list (guarantees, approval promises, superlatives, price claims) enforced in generation and validation | Restricted phrases never appear in an approved draft in the eval corpus | Deceptive-practice exposure from an AI-written promise | Lexicon enforced; eval corpus clean |
| CMP-7 | Accessibility conformance for the workspace | P2 | FE, DES | UX-1 | WCAG 2.2 AA audit and remediation | Audit findings remediated for core flows | Excluding reps who need assistive technology | Audit report with remediation evidence |

---

## 15. QA and evaluations (`QA`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| QA-1 | Golden conversation set | P0 | QA, AAI | DISC-2 | 300 de-identified multi-turn conversations spanning every stage and objection, with expert-written reference outcomes | Covers every state transition and objection class; refreshed quarterly | Evals that do not resemble reality | Set versioned, coverage report published |
| QA-2 | Automated eval harness in CI | P0 | QA, AAI | QA-1, AI-4 | Harness scoring groundedness, policy compliance, helpfulness, tone, and next-action correctness | No prompt or model change merges without a passing eval run; thresholds enforced | Quality regressions shipping unnoticed | Harness blocking merges; baseline scores recorded |
| QA-3 | Hallucination red-team suite | P0 | QA, AAI | AI-6 | Adversarial prompts designed to elicit invented prices, availability, approvals, and promises | 100% block or safe-deflect rate; any escape is a release blocker | The failure that ends the pilot | Suite green, escape count zero, re-run nightly |
| QA-4 | Prompt-injection and abuse suite | P0 | QA, SEC | AI-10 | Attacks embedded in customer messages, images, and shared listings | Zero policy bypasses and zero unauthorized tool calls | Customer-driven exploitation | Suite green in CI |
| QA-5 | Integration contract tests | P1 | QA, INT | CRM-1, INV-1 | Recorded-fixture contract tests per external system | Vendor API drift detected within a day | Silent breakage of availability or booking | Nightly contract run with alerting |
| QA-6 | Human review panel | P1 | QA, DS | QA-1 | Weekly blind review of 50 sampled drafts by two experienced reps | Inter-rater agreement tracked; findings feed the prompt backlog | Metrics that look good while customers feel spammed | Review cadence running with a published scorecard |
| QA-7 | Load, soak, and failure testing | P1 | QA, PLAT | ARCH-3 | Performance suite at 10x pilot volume, plus a 72h soak | Latency and error budgets met; no memory or queue growth over the soak | Evening peak collapse | Report filed with headroom numbers |
| QA-8 | Shadow-mode comparison | P0 | QA, DATA | ANL-3 | Pre-pilot mode generating drafts that are never shown, compared against what the rep actually sent | Groundedness and helpfulness measured before a single customer is affected | Learning on live customers | Two weeks of shadow data analyzed before the pilot opens |

---

## 16. Pilot (`PLT`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| PLT-1 | Store selection and agreements | P0 | DS, PM | CMP-5 | Two to three stores with mixed lead volume, signed agreements, and a named executive sponsor | Stores have sufficient volume for the power calculation in doc 07 | Underpowered pilot proving nothing | Agreements signed and volume verified against 90 days of history |
| PLT-2 | Baseline period measurement | P0 | DATA, PM | ANL-2 | Four weeks of pre-period metrics with no product exposure | Baseline is stable enough to detect the target effect | Comparing against a season, not a baseline | Baseline report accepted by PM and the GMs |
| PLT-3 | Rep training and change management | P0 | DS, DES | UX-1 | 90-minute training, a one-page quick reference, and an in-app tour | Every pilot rep passes a five-task practical check | Reps quietly reverting to the native inbox | Completion tracked at 100% with practical checks passed |
| PLT-4 | Experiment design and assignment | P0 | DATA, PM | DISC-4 | Assignment plan (matched pairs or stepped wedge), power calculation, and a pre-registered analysis plan | Pre-registered before the first treated conversation; contamination controls defined | Post-hoc metric shopping | Analysis plan committed to the repo with a timestamp |
| PLT-5 | Feedback loop and triage | P1 | DS, QA | UX-5 | In-app "this draft was wrong" reporting with a 24h triage SLA | Every report is triaged and categorized; fixes tracked to a prompt or tool change | Silent frustration | Triage board live with the SLA met |
| PLT-6 | Weekly pilot review ritual | P1 | PM, DS | ANL-2 | Weekly review with metrics, incidents, and top rep complaints | Decisions recorded with owners and dates | Drifting pilot with no decisions | Six consecutive reviews held with published notes |
| PLT-7 | Kill switch and rollback | P0 | PLAT, PM | ARCH-4 | Per-store and global switch that reverts to the native inbox with no data loss | Disable takes effect in under 60 seconds; threads remain readable and exportable | Being unable to stop quickly during an incident | Kill-switch drill executed and timed |

---

## 17. Deployment (`DEP`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| DEP-1 | CI/CD with progressive delivery | P0 | PLAT | ARCH-1 | Pipeline with tests, evals, canary, and automated rollback | Failed evals or error-budget burn stops the rollout automatically | Bad deploy reaching every dealer at once | Canary and auto-rollback demonstrated |
| DEP-2 | Observability stack | P0 | PLAT | ARCH-3 | Traces, metrics, structured logs, and an agent-run trace viewer | Any customer message can be traced end to end in under 2 minutes | Unexplainable behavior in front of a dealer | On-call resolves a synthetic incident using traces alone |
| DEP-3 | SLOs, error budgets, and alerting | P0 | PLAT | DEP-2 | SLOs for ingest, draft latency, send success, and integration freshness | Alerts are actionable with runbooks; no alert without an owner | Alert fatigue and missed outages | Runbooks linked from every alert |
| DEP-4 | On-call and support model | P1 | PLAT, DS | DEP-3 | Rota, escalation path, and a dealer-facing support channel with response targets | Dealer issues acknowledged within the target during store hours | Evening peak with nobody watching | Rota published; targets met for four consecutive weeks |
| DEP-5 | Tenant onboarding automation | P1 | PLAT, DS | META-1, CRM-1 | Guided onboarding for Page connect, inventory feed, CRM, calendar, and rep setup | A new store is live in under two hours with no engineer involved | Onboarding that only engineers can run, capping growth | Two stores onboarded by a non-engineer |
| DEP-6 | Backup, restore, and disaster recovery | P1 | PLAT, SEC | ARCH-2 | Backups with tested restore, defined RPO and RTO | Restore drill meets the stated RPO and RTO | Data loss with no recovery path | Drill completed with documented timings |

---

## 18. Optimization (`OPT`)

| ID | Item | P | Owner | Deps | Deliverable | Acceptance criteria | Key failure risks | DoD |
|---|---|---|---|---|---|---|---|---|
| OPT-1 | Draft acceptance improvement loop | P1 | AAI, DATA | ANL-3 | Pipeline mining rep edits into prompt and retrieval improvements | Measurable rise in acceptance rate and fall in edit distance across releases | Overfitting to a few loud reps | Two consecutive releases show improvement on the eval set and in production |
| OPT-2 | Model routing and cost reduction | P2 | AAI, PLAT | AI-9 | Task-appropriate routing with caching and distillation candidates | Cost per draft falls without an eval-score regression | Cheap models quietly degrading quality | Cost and quality reported together in one release note |
| OPT-3 | Send-time and cadence optimization | P2 | DATA, AAI | AI-8 | Reply-time modeling within policy and quiet-hours constraints | Response-rate lift proven by experiment, not by correlation | Optimizing into annoyance | Holdout experiment shows lift with no rise in opt-outs |
| OPT-4 | Multilingual support | P2 | AAI, QA | QA-1 | Spanish drafting with its own eval set and native reviewer | Eval thresholds met in Spanish before a single customer sees it | Shipping a language nobody on the team can check | Spanish eval suite green and reviewed |
| OPT-5 | Selective autonomy for low-risk intents | P2 | PM, AAI, LEG | QA-3, CMP-1 | Feature-flagged auto-send limited to an allowlist (for example acknowledgment and store hours) with dealer opt-in | Zero grounded-claim escapes over a defined observation period before any expansion of scope | Auto-send is where trust dies fastest | Written go or no-go decision backed by the observation data |
