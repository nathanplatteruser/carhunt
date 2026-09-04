# 06. Compliance and Security

**Research date: 2026-09-04.** Everything below is separated into three buckets: **Verified** (found in current sources, cited), **Assumption** (our design choice, not a legal requirement), and **Needs legal review** (a lawyer, not an engineer, decides).

> **Verification caveat, stated plainly.** `developers.facebook.com` and `ftc.gov` were not reachable from the build environment used to write this document, so several platform and regulatory items below were verified through current secondary sources rather than the primary page. Every one of those is marked `secondary` and carries a re-verification ticket in [09_OPEN_DECISIONS.md](09_OPEN_DECISIONS.md). No engineering work that depends on them should ship before someone opens the primary source and confirms.

---

## 1. Verified: Meta messaging rules

| # | Rule | Effect on LotBeacon | Confidence | Source |
|---|---|---|---|---|
| M1 | Businesses may reply within a **24-hour standard messaging window** from the customer's last message or qualifying action; the window resets on each new customer interaction | The inbox is organized around the window countdown. The send-service computes window state on every send | Verified `secondary` | [Meta Messenger Platform policy](https://developers.facebook.com/documentation/business-messaging/messenger-platform/policy.md/), [Chatimize summary 2026](https://chatimize.com/facebook-messenger-policy/) |
| M2 | Outside the window, only specific **non-promotional** message types are permitted | Follow-ups outside the window are limited to permitted types; marketing content outside the window is blocked by the rules engine | Verified `secondary` | Same as M1 |
| M3 | The **human agent** allowance extends the response window to **7 days** for genuine human-handled customer service, requires a real human rather than automation, and requires passing Meta App Review for the permission | Fits our draft-plus-human model, but it is not a license to automate. Auto-send must never use this path | Verified `secondary` | [Human agent permission guide](https://www.saurabhdhar.com/blog/human-agent-permission-meta-app-review), [Manychat window explainer](https://help.manychat.com/hc/en-us/articles/14281199732892-How-to-send-messages-outside-the-24-hour-and-7-day-windows-in-Messenger-and-Instagram) |
| M4 | Several legacy message tags (`CONFIRMED_EVENT_UPDATE`, `POST_PURCHASE_UPDATE`, `ACCOUNT_UPDATE`) are being **deprecated**, reported as **2026-01-12**, with **Utility message templates** as the replacement; templates need pre-approval, carry no promotional content, and have regional availability limits. Recurring Notifications are reported as deprecated around **2026-02-10** | Appointment confirmations and reminders must be built on the template path, not on legacy tags. Regional availability must be checked per store | Verified `secondary`, **high change risk** | [PPC Land on utility messages](https://ppc.land/meta-introduces-utility-messages-for-business-communication-compliance/), [Meta marketing messages FAQ](https://developers.facebook.com/documentation/business-messaging/messenger-platform/marketing-messages-on-messenger/faq.md/) |
| M5 | Misuse of tags or templates for promotional content is a common cause of app restriction | A single mislabeled follow-up can cost a dealer their messaging access. This is why `CMP-1` fails closed | Verified `secondary` | Same as M1 |
| M6 | One-time notification permits a single non-promotional follow-up after the window when the customer opts in during the window (Messenger only) | Optional v2 capability for "tell me when something like this arrives" | Verified `secondary` | Same as M1 |

**Design consequences**

1. The messaging-window state machine is a first-class service, not a helper function.
2. Every outbound message carries a `message_type` decision with the rule version that authorized it, stored in the audit log.
3. The platform policy set is versioned with an effective date and a named owner who re-verifies quarterly and on any deprecation notice.

---

## 2. Verified: reviews

| # | Rule | Effect | Confidence | Source |
|---|---|---|---|---|
| R1 | Google prohibits **review gating**: you may not pre-screen customers and solicit only the happy ones, or route unhappy customers to a private form instead of the public review path | The review workflow has no sentiment filter. Eligibility is transaction-based only | Verified `secondary` | [GBP review policy update](https://donhesh.com.au/blog/google-business-profile-review-policy-update-2025-2026/), [policy summary](https://canvasmasterseo.com/key-google-business-profile-review-policy-updates-2025-2026/) |
| R2 | Google prohibits **incentivized reviews**, including discounts, gift cards, contest entries, and other rewards for leaving, editing, or removing a review | The copy library contains no incentive language, and the restricted lexicon blocks it | Verified `secondary` | Same as R1 |
| R3 | Google prohibits **AI-generated reviews** and enforces on reviewing patterns, not only content | LotBeacon never drafts review text for a customer. It only sends a neutral ask with a link | Verified `secondary` | [Google review policy 2026](https://wiserreview.com/blog/google-review-policy/) |
| R4 | The FTC rule on the use of consumer reviews and testimonials (16 CFR Part 465) bans fake and materially misleading reviews, undisclosed insider reviews, and review suppression, with civil penalty exposure per violation. Reported effective **2024-10-21** | Employee and insider reviews are prohibited by policy. Suppressing negative feedback is prohibited | Verified `secondary`, primary text should be read before launch | [Review gating and the FTC rule](https://dodsonmc.com/review-gating-is-now-illegal/) |

**Design consequences**

1. `review_request` records prove that eligible customers were treated identically. The compliance test in `CMP-3` fails the build if a sentiment feature ever enters the eligibility query.
2. The complaint path is offered to everyone alongside the review ask, never instead of it for predicted detractors.
3. One ask plus at most one reminder per transaction, then permanent stop for that deal.

---

## 3. Verified: dealer data, privacy, and outbound contact

| # | Rule | Effect | Confidence | Source |
|---|---|---|---|---|
| D1 | Auto dealers that arrange financing or leasing are treated as financial institutions under GLBA and are subject to the **FTC Safeguards Rule**: a written information security program, a qualified individual, written risk assessments, access controls, encryption, MFA, service-provider oversight, incident response, training, testing, and secure disposal | LotBeacon is a service provider inside the dealer's program. We must be able to answer a dealer's vendor-security questionnaire on day one | Verified `secondary`, primary FAQ exists at ftc.gov | [FTC Safeguards FAQs for auto dealers](https://www.ftc.gov/business-guidance/resources/automobile-dealers-ftcs-safeguards-rule-frequently-asked-questions), [dealer compliance summary](https://www.terapartners.com/journal/ftc-safeguards-rule-auto-dealerships/) |
| D2 | Notification to the FTC is required for security events affecting 500 or more consumers, reported as within 30 days | Our incident-response runbook must meet the dealer's clock, which means our own notification-to-dealer SLA is much shorter | Verified `secondary` | Same as D1 |
| D3 | The FCC's TCPA **one-to-one consent rule was vacated** by the Eleventh Circuit on **2025-01-24** (*Insurance Marketing Coalition v. FCC*). Prior express written consent is still required for automated marketing calls and texts to mobile numbers | If and when SMS follow-up ships, consent capture and proof are mandatory. Messenger threads are not SMS consent | Verified `secondary` | [Wiley alert](https://www.wiley.law/alert-UPDATE-11th-Circuit-Vacates-FCCs-One-to-One-TCPA-Consent-Rule), [Morrison Foerster](https://www.mofo.com/resources/insights/250130-eleventh-circuit-vacates-fcc-s-tcpa-one-to-one-consent-rule) |
| D4 | The FTC **CARS Rule** was vacated by the Fifth Circuit in 2025, so it is not currently an enforceable obligation | Do not build to CARS-specific disclosure requirements yet, but do not build anything that would violate them either, since state analogues exist | Verified `secondary` | [FTC business guidance](https://www.ftc.gov/business-guidance/resources/automobile-dealers-ftcs-safeguards-rule-frequently-asked-questions), litigation summaries |
| D5 | California's bot disclosure law (SB 1001, B&P 17940-17943) makes it unlawful to use a bot to mislead a person about its artificial identity in order to incentivize a commercial transaction. Clear and conspicuous disclosure is the safe harbor | Where an automated experience talks directly to a customer, disclose. In draft-only mode a human sends every message, which materially reduces exposure, but any auto-send feature triggers this analysis | Verified `secondary` | [B&P 17941](https://california.public.law/codes/business_and_professions_code_section_17941), [practitioner guide](https://www.financierworldwide.com/bot-or-not-navigating-californias-bot-disclosure-law) |

---

## 4. Assumptions (our choices, not legal mandates)

| # | Assumption | Rationale | Revisit when |
|---|---|---|---|
| A1 | Draft-only for the entire pilot | The 4x hypothesis can be tested without autonomy, and autonomy multiplies every compliance risk | After zero grounded-claim escapes across the pilot |
| A2 | Message retention of 25 months, then hard delete, unless the dealer contract specifies otherwise | Long enough for a sales cycle plus a review period, short enough to limit breach blast radius | On the first dealer contract that demands otherwise |
| A3 | Trace and prompt logs retained 90 days, PII-redacted | Debugging window without a second copy of the customer database | On a security review finding |
| A4 | Maximum 3 unanswered outbound touches, then dormant | Reputation protection for the dealer Page | If experiments show a materially better cadence that does not raise opt-outs or blocks |
| A5 | Quiet hours 9pm to 8am local to the customer's store | Basic decency; also aligns with typical state telemarketing norms | On legal review of state-specific rules |
| A6 | No PII in prompts beyond first name, vehicle interest, and conversation content. No SSN, DOB, license, or financial account data ever enters the model context | Minimizes exposure through any model provider | Never loosen without security sign-off |
| A7 | Model providers contractually may not train on dealer or customer data | Table stakes for dealer trust | Per subprocessor change |
| A8 | The dealer is the controller, LotBeacon is the processor | Standard SaaS allocation | Legal review per jurisdiction |

---

## 5. Needs legal review

| # | Question | Why it matters | Blocking |
|---|---|---|---|
| L1 | Exact retention schedule per data class, including whether Meta's platform terms impose deletion obligations on message copies stored off-platform | Retention jobs cannot be finalized without it | `DATA-5`, pilot start |
| L2 | Whether the human agent path is appropriate for our exact product behavior, and what documentation Meta expects at App Review | Wrong answer means a rejected app or a policy violation | `META-8` |
| L3 | State-by-state applicability of telemarketing, auto-advertising, and AI disclosure laws for pilot store locations | Determines disclosure text and cadence rules | Pilot store selection |
| L4 | CCPA/CPRA and other state privacy law obligations, including whether any data flow constitutes a sale or share, and how opt-out propagates to the dealer's other vendors | Determines the request-handling runbook | `CMP-4` |
| L5 | Whether generated content constitutes dealer advertising under state law, and who is responsible for its accuracy | Determines the restricted lexicon and the indemnity split | `CMP-6`, contracts |
| L6 | Licensing terms for vehicle history and valuation data displayed inside a third-party workspace and quoted into Messenger | Redistribution can breach vendor contracts | `CRM-5` |
| L7 | Whether reps sending AI-drafted messages under their own name requires any disclosure in the customer's jurisdiction | Determines whether a footer or in-thread disclosure is needed | Pilot start |
| L8 | Recording, transcript, and consent implications when a Messenger thread is exported into the dealer's CRM | Dealer contract dependency | `CRM-2` |
| L9 | Minors: detection duty and handling when a customer appears to be under 18 | Escalation policy correctness | `WF-6` |

---

## 6. Security controls (summary)

| Domain | Control |
|---|---|
| Tenancy | Row-level security keyed on tenant, enforced in the database, with an automated cross-tenant test suite in CI |
| AuthN | SSO for dealer users, MFA required for admin and support roles |
| AuthZ | RBAC: rep sees own and team threads, manager sees store, admin sees tenant, support access is break-glass, time-boxed, and logged |
| Encryption | TLS in transit, managed-key encryption at rest, envelope encryption for Page tokens with scheduled rotation |
| Secrets | No secrets in code, scanner enforced in CI, short-lived credentials for service-to-service calls |
| Logging | PII masked by classification, no message bodies in application logs, redaction verified by scanner |
| Model calls | Redacted context, no training use, per-tenant cost and usage attribution, provider list published as subprocessors |
| Audit | Append-only hash-chained record of every send, approval, config change, and PII access, queryable per customer |
| Retention | Scheduled hard deletion across primary store, vector index, caches, and warehouse, with a completion report |
| Vulnerability management | Dependency scanning, SAST, annual third-party penetration test, critical and high findings remediated before GA |
| Incident response | Severity ladder, dealer notification SLA tighter than the dealer's own regulatory clock, tabletop exercise before pilot |
| Availability | SLOs on ingest lag, draft latency, and send success, with error budgets gating releases |

## 7. Customer-facing commitments

1. Every message a customer receives was approved and sent by a named human at the dealership.
2. Stop, unsubscribe, and any plain-language equivalent stop all outbound contact immediately, across channels.
3. We never ask for a social security number, date of birth, license image, or bank details inside Messenger.
4. Review requests are never conditioned on how happy we think a customer is, and never come with an incentive.
5. A customer can ask what the dealership has recorded about them and get an answer, because every remembered fact has a source.
