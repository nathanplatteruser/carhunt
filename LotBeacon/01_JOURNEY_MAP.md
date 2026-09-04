# 01. Journey Map

Two actors, one thread. The customer journey is what the buyer experiences. The rep journey is what happens inside LotBeacon during the same minute. Every stage lists the system trigger, the memory written, the grounding required, and the way this stage fails in the real world.

---

## Stage overview

| # | Stage | Customer state | Typical elapsed time | Primary system job |
|---|---|---|---|---|
| 0 | Ad or listing impression | Anonymous | Before contact | Attribution capture (`ref` / `m.me` parameter) |
| 1 | First inquiry | `NEW` | Minute 0 | Identify, ground the vehicle, draft an answer inside the reply window |
| 2 | Qualification | `QUALIFYING` | Minutes to hours | Fill the six qualifying slots without an interrogation |
| 3 | Vehicle discovery / alternates | `VEHICLE_MATCHED` | Hours to days | Inventory-grounded recommendations, real photos, honest gaps |
| 4 | Objection handling | `OBJECTION` | Any time | Classify objection, respond with facts or escalate to a human decision |
| 5 | Appointment / test drive booking | `APPOINTMENT_PROPOSED` -> `APPOINTMENT_SET` | Same day ideally | Offer real calendar slots, book, confirm, remind |
| 6 | Pre-visit confirmation | `APPOINTMENT_SET` | 24h and 2h prior | Confirm, re-confirm the vehicle is still available, log the answer |
| 7 | Visit outcome | `SHOWED` / `NO_SHOW` | Day of | Capture outcome from DMS/CRM, not from guesswork |
| 8 | Follow-up and nurture | `NURTURE` | Days to months | Cadence with real reasons to reach out, respecting the messaging window |
| 9 | Purchase outcome | `SOLD` / `LOST` | Day of deal | Write outcome, stop sales cadence, start post-sale track |
| 10 | Post-sale care | `POST_SALE` | Delivery + 1 to 7 days | Delivery check-in, open items, service handoff |
| 11 | Review request | `REVIEW_REQUESTED` | Post-delivery or post-service | One neutral, non-incentivized ask, one reminder maximum, then stop |
| 12 | Dormant / closed | `CLOSED`, `DO_NOT_CONTACT` | Anytime | Suppression, retention clock, deletion on request |

---

## Stage detail

### Stage 1. First inquiry

| Field | Detail |
|---|---|
| Trigger | Messenger webhook `messages` event on a dealer Page, often prefilled with "Is this still available?" |
| System actions | Resolve PSID -> person -> existing CRM contact. Fetch the referenced vehicle by listing ref or by parsing the shared listing card. Check live availability. Assemble Fact Ledger. Draft reply. Put thread at the top of the rep's inbox with a reply-window countdown. |
| Memory written | `thread.origin`, `vehicle_interest[0]` with provenance, `first_contact_at`, attribution ref |
| Grounding required | Availability, price, mileage, VIN, one deal-relevant disclosure (title brand if the store sells branded units) |
| Human gate | Rep reviews and sends. Always, in v1. |
| Failure modes | Vehicle already sold and the feed is stale; the customer asks about a unit from another rooftop; the message is spam or a scam probe; the "customer" is a vendor pitching the dealer |
| Guardrail | If availability confidence is stale beyond the configured freshness SLO, the draft says the rep is confirming, and the workspace shows a stale-data warning instead of asserting availability |

### Stage 2. Qualification

Six slots, gathered conversationally, at most two questions per message.

| Slot | Why it matters | Never do |
|---|---|---|
| Use case and must-haves (seats, tow, AWD, car seats) | Drives alternates when the unit sells | Ask for a spec sheet the customer does not have |
| Budget frame (cash price, or monthly plus down) | Routes to desking correctly | Quote a payment from the model |
| Trade-in presence (year, model, mileage, payoff) | Trade is half of used-car deals | State a trade value from the model |
| Timeline | Prioritization signal | Pressure language |
| Financing intent (cash, own bank, dealer arranged) | Determines the next handoff | Predict approval or rate |
| Location and travel willingness | Filters cross-market leads | Ask for a home address in Messenger |

Notes: the assistant only asks for information it will actually use in the next step, and it never asks for SSN, date of birth, driver's license images, bank details, or full credit application data inside Messenger. Those go to the dealer's secure application link.

### Stage 3. Vehicle discovery and alternates

| Field | Detail |
|---|---|
| Trigger | Slots filled to threshold, or the vehicle of interest is unavailable |
| System actions | Structured inventory query using slot filters. Rank by fit, then by dealer merchandising priority (aged units, floorplan cost), which is a configurable weight, not a hidden nudge. Attach real photo URLs and the VDP link. |
| Memory written | `vehicle_interest[]` with fit reasons and rejections, `rejected_reason` per unit |
| Grounding required | Every attribute stated (trim, mileage, drivetrain, price, seats, title status) must exist in the inventory record |
| Failure modes | Recommending a unit at a sister store the customer cannot see, listing a feature the trim does not have, hallucinated third row or tow package |
| Guardrail | Spec claims are limited to fields present in the inventory feed plus a curated spec table. Anything outside that answers "I will confirm with the vehicle in front of me" |

### Stage 4. Objection handling

| Objection class | Grounded answer source | Escalation rule |
|---|---|---|
| Price too high | Listed price, current published offers, comparable inventory | Any discount discussion escalates to the rep with a "no authority" banner |
| Payment too high | Nothing generated. Route to desking or the dealer payment calculator | Always human |
| Trade value | Authoritative valuation tool range only, marked as an estimate pending inspection | Human sign-off before any number is sent |
| Credit worry | Approved disclosure text plus the secure application link | Never predict approval |
| Vehicle history, accidents, title brand | Vehicle history report summary, title status field | Human review if the report and the feed disagree |
| Distance and delivery | Store policy record | Human if the request is outside written policy |
| "Still shopping" | Nurture path with a genuine reason to follow up | None |
| Warranty and as-is | Store policy record and the posted Buyers Guide status | Human on any implied promise |

### Stage 5. Appointment and test drive

| Field | Detail |
|---|---|
| Trigger | Intent score crosses threshold, or the customer asks about seeing the vehicle |
| System actions | Read real availability from the dealer calendar. Offer two or three concrete slots. Book on confirmation. Write the appointment to CRM. Schedule confirmations. |
| Memory written | `appointment{id, start, vehicle, type}`, `commitments[]` (for example "hold the unit until 6pm") |
| Grounding required | Slot existence, store hours, whether the specific unit is on the lot or in transit, whether a test drive requires a license and insurance per store policy |
| Failure modes | Double booking, offering a slot outside store hours, booking a test drive for a vehicle that is at recon or at another rooftop |
| Guardrail | Booking is a two-phase commit: hold, confirm, write. On calendar write failure the rep gets an alert and the customer gets a human-sent correction |

### Stage 6 to 7. Confirmation and visit outcome

Confirmations are non-promotional and must respect the messaging window rules in [06_COMPLIANCE_SECURITY.md](06_COMPLIANCE_SECURITY.md). Outcome (`SHOWED`, `NO_SHOW`) comes from CRM or an explicit rep tap, never inferred from silence alone. A `NO_SHOW` triggers a single low-pressure rebook offer, not a cadence.

### Stage 8. Follow-up and nurture

| Cadence rule | Value |
|---|---|
| Maximum outbound touches without a customer reply | 3, then the thread goes dormant |
| Minimum spacing | 48h, unless the customer asked for a specific date |
| Requires a reason | Yes. Price change, new arrival matching the slots, unit sold, appointment reminder. No "just checking in" as the only content |
| Window compliance | Outside the standard reply window, only the permitted non-promotional path applies. See doc 06 |
| Stop conditions | Any opt-out phrase, `DO_NOT_CONTACT`, sold elsewhere, negative sentiment threshold, rep override |

### Stage 9 to 11. Outcome, post-sale, review request

| Field | Detail |
|---|---|
| Sold trigger | DMS deal record or explicit rep confirmation. Never inferred from conversation text alone |
| Post-sale track | Delivery-day thank you, open-items checklist (second key, plates, we-owe items), service department handoff |
| Review eligibility | Delivered deal, `open_we_owe == false`, no open complaint, no unresolved escalation, no prior review request within the configured cooldown |
| Review request rules | Sent to **all** eligible customers, not only the happy ones. No incentive, no scripted wording for the customer, no pre-screening question that routes unhappy customers away from the public review path. One ask, one optional reminder, then never again for that transaction |
| Complaint path | A separate, always-available "tell us what went wrong" route may exist, but it is offered to everyone alongside the review ask, not instead of it for predicted detractors |
| Memory written | `review_request{sent_at, channel, platform, response}` for audit |

### Stage 12. Dormant, closed, deleted

Opt-out is honored on any channel and propagates to CRM within the sync SLO. Deletion requests follow the retention schedule in doc 06. Suppression is a hard block enforced at the send layer, not a UI hint.

---

## Rep journey, one shift

| Time | What the rep does | What LotBeacon does |
|---|---|---|
| Shift start | Opens the workspace | Inbox sorted by a priority score that blends reply-window urgency, intent, deal value, and staleness |
| First 20 minutes | Clears the red band (window expiring, hot intent) | Drafts pre-generated with fact ledgers attached, one keystroke to send or edit |
| Mid-shift | Works the floor | Threads keep accruing drafts. Nothing sends. Badge counts by urgency band |
| Between customers | Triages on mobile | Summary-first view, three-line recap, next best action, one-tap send |
| Objection arrives | Reads the risk banner | Draft marked "needs your call", numbers suppressed, desk manager tag available |
| End of shift | Sets follow-ups | Commitments ledger shows every promise made today with due dates and owner |
| Manager view | Coaches | Escalation queue, drafts edited heavily (voice mismatch), threads at risk, review-request compliance |
