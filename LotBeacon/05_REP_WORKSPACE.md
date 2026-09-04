# 05. Rep Workspace

Design goal: a rep with 40 open threads spends their attention where it converts, and every send is a deliberate act that takes one keystroke.

## 1. Layout

```
+------------------------------------------------------------------------------+
| LotBeacon   [Store v]  [My threads | Team]  [Search]        [Rep] [Human-only]|
+---------------+--------------------------------------+-----------------------+
| INBOX         | CONVERSATION                          | CONTEXT               |
|               |                                       |                       |
| [Now  4]      | Sarah M.  - QUALIFYING  - reply 3h12m | Customer profile      |
| [Today 11]    |                                       |  Budget 25-30k (2d)   |
| [Waiting 7]   | Recap                                 |  Trade 2016 Odyssey   |
| [Nurture 22]  |  Wants 3-row under 30k, has a trade,  |  Timeline: 2 weeks    |
|               |  worried about the third-row size,    |  Financing: dealer    |
| Sarah M.  92  |  asked about Saturday.                |  Sentiment: positive  |
|  3-row, trade |                                       |                       |
|  reply in 3h  | [full transcript v]                   | Vehicle context       |
|               |                                       |  #A4471 Expedition Max|
| Dave R.   88  | DRAFT (grounded, 1 warning)           |  Available 2m ago     |
|  price obj    |  Hi Sarah - the Expedition Max        |  $28,995 - 84,120 mi  |
|               |  (#A4471) is still here. It has the   |  Clean title          |
| Nina T.   71  |  bigger cargo area behind the third   |  [photos] [VDP]       |
|  no-show      |  row that you asked about. Could you  |                       |
|               |  do Saturday at 10 or 11:30?          | Next best action      |
|               |                                       |  Book the test drive  |
|               |  ! Trade value needs your call        |  Why: 3 slots filled, |
|               |                                       |  asked about Saturday |
|               | [Send] [Edit] [Regenerate] [Escalate] |                       |
|               |                                       | Commitments (1 due)   |
|               |                                       |  Send 3rd-row photos  |
+---------------+--------------------------------------+-----------------------+
```

## 2. Prioritized inbox

| Band | Meaning | Sort within band |
|---|---|---|
| **Now** | Reply window closing, hot intent, escalation, or an overdue commitment | Time remaining ascending |
| **Today** | Active conversations awaiting a reply | Priority score descending |
| **Waiting** | Customer's turn to answer | Last activity descending |
| **Nurture** | Dormant or scheduled follow-up | Next due ascending |

Priority score inputs, all visible on hover: reply-window time remaining, intent score, appointment proximity, deal value, days since last touch, sentiment risk, commitment overdue. The score is explainable in one sentence ("Window closes in 41 minutes and she asked a direct question"). Sort is stable: new arrivals highlight in place rather than reordering under the cursor.

## 3. Panels

| Panel | Contents | Rules |
|---|---|---|
| Recap | Three lines: situation, open question, next action | Regenerated on every inbound message; every claim traces to the thread or the ledger |
| Transcript | Full history with inline fact citations on dealer statements | Collapsed by default |
| Customer profile | Typed slots with age, confidence, and source-on-hover | Stale slots visibly dimmed; conflicts shown as a two-value chooser |
| Vehicle context | Cards for each vehicle of interest with live availability and freshness age, price, key specs, photos, VDP link | Availability older than the TTL renders as "confirming" not "available" |
| Intent and lead state | Current state, intent, sentiment trend, objection log | State changes are clickable to their causing event |
| Next best action | One recommendation with a reason string and a one-click execution | Rep can dismiss with a reason, which is training signal |
| Commitments | Due and overdue promises with snooze and complete | Overdue items pin to the top of the inbox |
| Draft editor | Editable body, warnings, fact panel, send controls | Blocked drafts cannot be sent until resolved |

## 4. Warning system

| Badge | Trigger | Rep must |
|---|---|---|
| 🟢 Grounded | Every restricted claim matched to a fresh ledger entry | Nothing. Read and send |
| 🟡 Low confidence | Intent abstain, ambiguous request, or a stale slot relied upon | Read carefully before sending |
| 🟠 Stale data | A ledger entry is past its TTL | Refresh or reword |
| 🔴 Blocked | Unverified claim, restricted promise, or negotiation content | Supply the fact, or write that sentence yourself |
| ⚫ Human-only | Escalation trigger fired | Handle personally. No draft is offered |

Warning discipline: at most one warning banner is shown at a time, ranked by severity, with a specific sentence highlighted in the draft. Generic "AI can make mistakes" text is banned because it trains reps to ignore banners.

## 5. Actions

| Action | Shortcut | Behavior |
|---|---|---|
| Send | `Cmd/Ctrl + Enter` | Approval record written, send-service checks window and suppression, 10-second undo |
| Edit and send | `E` | Edit distance captured as quality signal |
| Regenerate with instruction | `R` | "Shorter", "warmer", "answer the cargo question", free text |
| Escalate | `Cmd/Ctrl + Shift + E` | Routes to manager or desk with a reason, sets `ESCALATED` |
| Human-only toggle | `H` | Assistant stops drafting for this thread until toggled back |
| Book test drive | `B` | Inline slot picker, two-phase commit, writes to CRM |
| Snooze thread | `S` | Sets a follow-up with a required reason |
| Mark wrong | `W` | Files a draft-quality report with the trace attached |

## 6. Test-drive CTA

The booking widget is inline, never a separate app. It shows real slots from the store calendar, the vehicle it is booked against, and what the customer should bring per store policy. On confirmation it writes the appointment, adds the confirmation follow-ups, sets the state, and posts the activity to CRM. If any write fails, the rep sees a red banner with a single retry and the customer receives nothing until it succeeds.

## 7. Manager console

| View | Purpose |
|---|---|
| Escalation queue | Threads needing a human decision, with age and SLA |
| At-risk threads | Negative sentiment, unanswered beyond target, overdue commitments |
| Quality outliers | Reps with unusually high edit distance (voice mismatch) or unusually high blind-send rate (rubber-stamping) |
| Review compliance | Proof that review requests went to all eligible customers with no sentiment filtering |
| Capacity | Concurrent threads per rep against the 4x hypothesis targets in doc 07 |

## 8. Accessibility and mobile

Core loop (read recap, check warning, approve, send) must be operable one-handed on a phone and fully keyboard navigable on desktop. Target WCAG 2.2 AA for the core flows: color is never the only signal (every badge carries text), focus order follows reading order, and all controls are labeled.
