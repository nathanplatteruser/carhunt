# LotBeacon

**An AI reply assistant for used-car sales reps working Facebook Messenger leads.**

LotBeacon keeps per-customer memory (vehicle interest, objections, commitments, sentiment, next action), grounds every factual claim in an authoritative system, drafts a reply the rep can edit, and never sends anything a human did not approve in the pilot configuration. The product hypothesis is that a rep can carry **4x the concurrent Messenger conversations** at equal or better appointment quality. This folder is the implementation blueprint that either proves or disproves that.

> **Repo placement note.** This blueprint was requested as a private repository. It currently lives as a folder inside the public `carhunt` repo, so treat nothing here as confidential until it is moved. To make it private: create an empty private repo `LotBeacon` under `nathanplatteruser`, copy this folder in as the repo root, commit, and delete the folder from `carhunt`.

---

## Document index

| # | Document | What it answers |
|---|---|---|
| 1 | [01_JOURNEY_MAP.md](01_JOURNEY_MAP.md) | Customer and rep journey, stage by stage, with system behavior and failure mode at each step |
| 2 | [02_BACKLOG.md](02_BACKLOG.md) | 18 workstreams, ticket-ready, with priority, owner, dependencies, deliverable, acceptance criteria, risks, definition of done |
| 3 | [03_ARCHITECTURE.md](03_ARCHITECTURE.md) | Services, data model, identity, memory tiers, customer state machine, agent runtime, tools, escalation, retries, observability, audit |
| 4 | [04_GROUNDING.md](04_GROUNDING.md) | Claim taxonomy and the fact-ledger pipeline that blocks unverified statements about inventory, price, trade, financing, policy, appointments, warranty |
| 5 | [05_REP_WORKSPACE.md](05_REP_WORKSPACE.md) | Inbox prioritization, conversation summary, customer profile, vehicle context, next-best-action, editable draft, confidence warnings, override |
| 6 | [06_COMPLIANCE_SECURITY.md](06_COMPLIANCE_SECURITY.md) | Meta messaging rules, consent, opt-out, retention, access control, security obligations, review-platform policy. Verified vs assumed vs needs legal review |
| 7 | [07_KPIS_EVALS.md](07_KPIS_EVALS.md) | KPI tree, the eval harness, the experiment that tests the 4x claim honestly |
| 8 | [08_ROADMAP.md](08_ROADMAP.md) | MVP scope, 30/60/90 roadmap, pilot design, launch gates, top risks, the 10 tickets to start tomorrow |
| 9 | [09_OPEN_DECISIONS.md](09_OPEN_DECISIONS.md) | Every unresolved decision, with owner and the date it blocks |

---

## Product principles

1. **Humans send the messages.** The pilot ships draft-only. Auto-send is a later, narrowly scoped, feature-flagged capability with an explicit dealer opt-in and a per-intent allowlist.
2. **No claim without a lookup.** Availability, price, payments, trade value, fees, warranty, appointment times, and store policy come from a system of record or they do not get said. See [04_GROUNDING.md](04_GROUNDING.md).
3. **Memory is evidence, not vibes.** Every profile slot stores the message it came from. Contradictions surface to the rep instead of being silently overwritten.
4. **Not a fake human.** The assistant writes in the rep's voice for the rep to send. Where an automated experience talks directly to a customer, it is disclosed.
5. **Reviews are earned, never gated.** Requests go to every eligible customer regardless of predicted sentiment, with no incentive attached.
6. **The rep can always take the wheel.** One click puts a thread in human-only mode and the assistant stops drafting.

## Scope boundaries for v1

| In scope | Out of scope for v1 |
|---|---|
| Facebook Messenger threads on dealer-owned Pages | Instagram DM, WhatsApp, SMS, web chat (v2 channel adapters) |
| Used-vehicle retail sales conversations | Service scheduling, parts, wholesale, commercial fleet |
| English | Spanish (v2, requires its own eval set and a fluent reviewer) |
| Draft generation with rep approval | Autonomous sending, autonomous price negotiation, credit decisions |
| Appointment proposal and booking against a dealer calendar | Desking, F&I product presentation, contract generation |
| Post-sale review request orchestration | Review response management, reputation reporting suite |

## Naming

**LotBeacon**: the lot is the inventory, the beacon is the assistant that tells a rep which conversation deserves the next five minutes.
