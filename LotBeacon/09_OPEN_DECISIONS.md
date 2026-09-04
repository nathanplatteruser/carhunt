# 09. Open Decisions

Every unresolved decision that a person, not a document, has to make. Nothing here is settled. Anything marked **blocking** stops the referenced work.

## A. Verification debt (highest priority)

| ID | Decision | Why it is open | Blocks | Owner | Needed by |
|---|---|---|---|---|---|
| OD-1 | Re-verify every Meta messaging rule in doc 06 section 1 against the primary Meta developer documentation, and record the doc version and access date | The build environment could not reach `developers.facebook.com`, so those rows are secondary-sourced | `META-3`, `META-4`, `CMP-1`, top ticket 6 | LEG + INT | Before any send-path code merges |
| OD-2 | Confirm the exact deprecation dates and regional availability of the utility template path for appointment confirmations | Reported as 2026-01-12 for legacy tags, and availability is region-limited. Wrong assumption breaks reminders mid-pilot | `META-4`, `WF-4` | INT | Before pilot |
| OD-3 | Confirm the human-agent permission requirements and whether our exact product behavior qualifies | Determines the App Review narrative and whether 7-day handling is available at all | `META-8` | LEG | Before App Review submission |
| OD-4 | Read the primary FTC text on consumer reviews and testimonials and the Safeguards Rule FAQs, and record obligations that fall on us as a service provider | Secondary sources agree, but penalties attach to the primary text | `CMP-3`, `SEC-7` | LEG | Before pilot |

## B. Product and scope

| ID | Decision | Options | Trade-off | Owner | Needed by |
|---|---|---|---|---|---|
| OD-5 | Does v1 ever auto-send anything, even an acknowledgment | (a) never, (b) acknowledgment only behind dealer opt-in | (a) is safest and keeps the pilot clean; (b) improves first-response time, which is the strongest conversion lever | PM + LEG | Day 30 |
| OD-6 | Do we support cross-rooftop inventory quoting in v1 | Yes with disclosure, or no | Yes widens the match rate, no avoids promising a car the customer cannot drive today | PM | Day 45 |
| OD-7 | Do we ever surface a trade range in Messenger, or always defer to an appraisal | Range with human approval, or defer entirely | Ranges move deals forward and are also the fastest way to create a number the store will not honor | PM + Dealer GM | Day 45 |
| OD-8 | Is the assistant's voice the rep's voice or the store's voice | Per-rep tone profiles, or a store-standard voice | Per-rep drives acceptance and authenticity, store-standard is easier to govern and audit | DES + PM | Day 30 |
| OD-9 | Who owns the customer relationship if a rep leaves | Thread reassignment defaults | Affects memory portability, customer experience, and the dealer's pay plan politics | PM + Dealer GM | Day 60 |
| OD-10 | Do we build an SMS channel in year one | Yes or no | SMS multiplies reach and multiplies TCPA consent exposure. Messenger consent is not SMS consent | PM + LEG | Q2 planning |

## C. Technical

| ID | Decision | Options | Trade-off | Owner | Needed by |
|---|---|---|---|---|---|
| OD-11 | Primary and fallback model providers, and the routing policy per task | Single frontier provider, or mixed with small models for classification | Cost and latency versus quality and operational simplicity | AAI | Day 21 |
| OD-12 | Vector store choice for archival retrieval | pgvector in the primary database, or a dedicated service | pgvector keeps tenancy enforcement in one place; a dedicated store scales further but duplicates the isolation problem | PLAT | Day 30 |
| OD-13 | Event bus technology | Managed queue with an outbox, or a log-based broker | Ordering guarantees per thread versus operational overhead | PLAT | Day 14 |
| OD-14 | Does the claim validator use a deterministic extractor, a model extractor, or both | Both, with deterministic for numeric and identifier classes | Both is safest and costs latency; the numeric path must never be model-only | AAI | Day 21 |
| OD-15 | How long is the grounding cache TTL per claim class | Values proposed in doc 04 | Shorter TTL means more vendor API calls and possible rate limits; longer TTL means stale answers | AAI + INT | Day 30 |
| OD-16 | Do we store message media ourselves or reference platform URLs | Store, or reference | Storing protects against URL expiry and adds retention and security obligations | PLAT + SEC | Day 30 |

## D. Data, legal, and commercial

| ID | Decision | Options | Trade-off | Owner | Needed by |
|---|---|---|---|---|---|
| OD-17 | Final retention schedule per data class | Proposed 25 months for messages, 90 days for traces | Longer aids analytics and disputes, shorter reduces breach blast radius and request burden | LEG + Dealer | Before pilot |
| OD-18 | Whether dealer data may be used, in aggregate and de-identified, to improve prompts or models | Yes with contractual permission, or never | Improvement loop quality versus dealer trust and contract complexity | LEG + PM | Contract drafting |
| OD-19 | Pricing model: per rep, per conversation, per appointment, or per delivered unit | Any | Per appointment aligns incentives best and is the hardest to attribute cleanly | PM + Finance | Day 60 |
| OD-20 | Who is accountable for a message a rep approved that turns out to be wrong | Dealer, LotBeacon, or shared with defined caps | Drives the indemnity clause and how aggressive the restricted lexicon should be | LEG | Contract drafting |
| OD-21 | Which review platforms are supported at launch and in what order | Google first, then others | Each platform has its own solicitation rules that must be encoded separately | PM + LEG | Day 60 |
| OD-22 | SOC 2 timing | Start in year one, or after GA | Dealer groups increasingly require it; it costs engineering time during the build | SEC + PM | Q2 planning |

## E. Measurement

| ID | Decision | Options | Trade-off | Owner | Needed by |
|---|---|---|---|---|---|
| OD-23 | Final wording of "handled conversation" and whether an outbound-only day counts | Proposed definition in doc 07 | Too loose and 4x becomes meaningless; too strict and real work goes uncounted | PM + DATA | Before baseline starts |
| OD-24 | Does the pilot use matched pairs, a stepped wedge, or both | Both, as proposed | Both is the most defensible and the most operationally demanding | DATA | Before pilot |
| OD-25 | What multiple counts as success if 4x is not reached | Written threshold agreed in advance | Agreeing after the fact is how pilots turn into marketing | PM + Exec sponsor | Before pilot |

---

## Standing watch items

| Item | Cadence | Owner |
|---|---|---|
| Meta platform policy and deprecation review | Quarterly, plus on any announcement | INT |
| Review-platform solicitation policy review | Quarterly | LEG |
| State AI disclosure and privacy law tracking for active markets | Quarterly | LEG |
| Model provider terms and subprocessor changes | On change | SEC |
| Golden eval set refresh from live traffic | Quarterly | QA |
