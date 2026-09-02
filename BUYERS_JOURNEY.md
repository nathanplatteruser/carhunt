# CarHunt and the Human Side of Buying a Truck
### A field report from Lincoln, Nebraska: how I shopped 700 vehicles with software and bought the one with photos

---

## Part 1: What CarHunt is, in plain English

Shopping Facebook Marketplace for a family SUV feels like drinking from a firehose. Every listing looks the same at 10pm on a phone, prices are all over the map, and by the time you circle back to "the good one," it's sold. I'm a data guy, so I did what data guys do: I taught my computer to handle the tedious part. Here is everything it does, no jargon:

1. **It reads the listings so we don't have to.** Every week it looks at Facebook Marketplace across five metros (Lincoln–Omaha, Denver, Kansas City, Des Moines, and Minneapolis–St. Paul) and writes down every full-size 3-row SUV and half-ton truck between $20k and $50k. Right now that's about 740 vehicles.

2. **It figures out what each one is actually worth.** For every year, model, and trim it keeps a fair private-party value (anchored to the same KBB and Edmunds numbers a dealer would use), adjusts for mileage, and knocks 25% off anything with a rebuilt or salvage title. Then it compares the asking price to that number.

3. **It scores every vehicle 0 to 10** on discount vs. market, cost per remaining mile, model quality, distance from home, listing legitimacy, and title status. A 9 is a screaming deal. A 3 is a seller who loves their truck more than the market does.

4. **It tells the truth about dead inventory.** Listings that sold get a big red **SOLD** tag instead of quietly disappearing, because a deal list full of ghosts wastes everyone's evening. In one audit, 1 in 5 "available" listings had already sold.

5. **It answers family questions a listing won't.** Every vehicle is tagged for guaranteed 3rd-row seating and for cargo space behind that 3rd row, because a Suburban swallows a stroller and the team's gear, and a standard-length SUV does not.

6. **It never, ever messages anyone.** The tool drafts a polite opening message for each listing, but every single one is reviewed, edited, and sent by me, personally, on my own schedule. More on why that matters below. It turned out to be the whole ballgame.

The whole thing lives on a free public webpage that updates when I re-run it, and works the same on my phone in the service-lane waiting room as it does on my desktop.

## Part 2: How I actually use it (the 15-minute routine)

1. Open the dashboard. Filter: **3rd row GUARANTEED**, **Cargo XL**, **Hide sold**.
2. Sort by score. Look at the top ten. Anything new since last week jumps out.
3. Click **✕** on anything I know I don't want. It's gone forever, even after next week's refresh.
4. For anything interesting: read the value math, check the title status, and if it's a rebuilt title, open the auction-history link to see the actual pre-repair damage photos before forming an opinion.
5. Click **Draft DM**, edit the message so it sounds like me, copy it, and send it myself on Facebook. Then click **✓ messaged**, and the row moves to my "waiting on seller" pile so the main list only ever shows fresh prospects.
6. Come back when sellers reply. Repeat weekly. Total time: about 15 minutes, instead of the two hours of doomscrolling it replaced.

## Part 3: What the data could not decide

Here's the part that surprised me, and the reason this document exists.

The software ranked hundreds of vehicles. But the vehicle I bought, a Ford Expedition, **was not the highest-scored vehicle on my board.** The scoring got me a smart shortlist. A human being closed the deal. My funnel, as an ordinary buyer:

- **~20** sellers and dealers I messaged with a personal, specific note
- **~10** ever responded at all
- **~4** were actually forthcoming, willing to talk pros *and* cons of their own vehicle
- **2–3** worked with my genuinely inconvenient schedule to get me a test drive
- **1** (exactly one) showed me the recent repairs and reconditioning they'd done, with photos the rep took himself

That last one got my money, on the spot, in about 30 minutes.

Every dealership reconditions its inventory. Only one showed me. Not a line on a window sticker that says "inspected," but actual pictures of actual work on the actual truck I was about to buy, sent by the person selling it to me. That told me three things no spec sheet can: they maintained the vehicle, they were proud of it, and the rep knew the details cold instead of talking at a high level. Trust, confidence, validation. Green light after green light. Nobody pushed me anywhere. I just kept wanting the next step.

## Part 4: What I learned about how buyers like me decide

1. **Timely beats instantaneous.** An auto-reply in 4 seconds reads as a bot. A real answer in a few hours reads as a person. No reply at all reads as "we don't want your money." Half my messages were simply ghosted, and that's half the market forfeiting the game.
2. **Canned messages are visible from space.** The note that wins acknowledges *my* question about *this* truck. My own tool drafts messages for me, and I still rewrite every one, because people buy from people.
3. **Honesty about cons is a feature.** The sellers willing to say "the second-row latch sticks, here's the part number" instantly outranked the ones who said "runs great" and changed the subject.
4. **Show the work.** Photos of the repairs you already did cost you five minutes and won a same-day decision over 19 competitors. That's the cheapest marketing in the automotive industry.
5. **The index finds the shortlist. The human wins the sale.** Data narrowed 740 vehicles to 20 conversations. A rep with a camera and some pride turned one conversation into a handshake.

---

*Appendix for the curious: the tool is a small set of Python scripts and one self-contained webpage in this repository. A scraper reads listing tiles, a valuation table covers each model, year, and trim, a scoring formula ranks everything, and a dashboard provides the filters described above. No accounts, no tracking, nothing sold. It's one buyer's homemade fishing rod. Live board: https://nathanplatteruser.github.io/carhunt/ (Nathan Platter, Lincoln, NE, September 2026)*
