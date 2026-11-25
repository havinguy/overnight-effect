# The Overnight Effect in Vietnam: Real, Regime-Dependent, and Hard to Capture

*A measurement study of close-to-open vs. open-to-close returns on the Ho Chi Minh Stock Exchange (HOSE), 2011–2026.*

---

## The puzzle

In most developed markets, almost all of the stock market's long-run return has arrived overnight — between yesterday's close and today's open — while the trading day itself, open to close, has gone roughly nowhere. The pattern was first noted by French and Roll in 1986 and documented across strategies and countries by Lou, Polk and Skouras (2019). It turns up in all 23 developed markets of the MSCI World index.

Then there is China, the great exception. Chinese overnight returns are, on average, *negative*. Researchers trace it to the settlement rule: for most of its history China ran a T+1 system that bars you from selling a stock the same day you buy it, which pushes a discount onto the open.

Vietnam sits in between. It is a frontier, retail-driven market that runs **T+2 settlement** — you cannot sell until two days after you buy. So before looking at any data, the sign was genuinely open: would Vietnam look like the developed world (positive overnight) or like China (negative overnight)?

This project set out to answer that cleanly, and then to ask the harder second question: even if the pattern exists, can anyone actually *capture* it?

## What we measured

Every daily return splits exactly into two legs, in logs:

- **Overnight:** `ln(Open_today) − ln(Close_yesterday)`
- **Intraday:** `ln(Close_today) − ln(Open_today)`

We computed each leg's mean, volatility, Sharpe-like ratio and significance across three levels:

- **Level A — the indices** (VN-Index back to 2011, VN30 back to 2018).
- **Level B — individual stocks** (the VN30 constituents, rebuilt point-in-time to avoid survivorship bias).
- **Level C — VN30 futures** (VN30F1M, the one instrument where the overnight trade is actually executable, since futures settle T+0).

The study is deliberately framed as **measurement first**. Whether the pattern exists is a different question from whether you can trade it, and mixing the two is how people fool themselves. Tradability got its own phase.

A note on rigor, because it is the point. Decision rules were pre-registered in each script's header *before* the run. Inference uses Newey–West and block-bootstrap standard errors. Multiple-comparison bars (Bonferroni) were applied to the weekday grids. Every single number in this write-up is tied to a claim in a public register, each with a confidence interval and a status of *supported*, *undetermined*, *untestable* or *retired*. Several of our own early conclusions ended up *retired* — more on that below.

## Finding 1: the overnight leg wins — but read the fine print

Over the full VN-Index sample (2011–2026), the overnight leg beats the intraday leg, and it does so as the *calmer* of the two:

- Overnight: **+5.2 bp/night** (t = 4.8)
- Intraday: **−1.9 bp/day** (t = −1.2, not significant)
- Difference: **+7.1 bp** (t = 3.8)
- Annualised Sharpe-like ratio: **1.51 overnight vs −0.22 intraday**; overnight volatility is *lower* (0.59% vs 1.05% daily).

So on the headline, Vietnam looks like a developed market, not like China. The China-style negative overnight does not appear.

But the honest version is narrower. When you drop weekend-spanning nights and look only at ordinary one-day nights, the overnight-minus-intraday gap collapses to **+1.4 bp (t = 0.66)** — not significant. A large part of the full-sample difference is a **weekend effect**: the trading session right after a weekend loses about **22 bp** on average. That is a real feature, but it is not the clean "overnight always wins" story the headline implies, and we flag it as a post-hoc discovery rather than something we set out to test.

## Finding 2: the effect is regime-dependent — and 2022 is the hinge

This is the central result. The overnight premium is not a constant of the Vietnamese market. It switches on.

On a point-in-time, free-float cap-weighted VN30 stock basket (validated to track the published index at a correlation of **0.9970**), the overnight return is **indistinguishable from zero before 25 August 2022** and **about +13.5 bp per night after it**. And it is not a free lunch appearing from nowhere — it is a **relocation**:

| Leg | Before 2022-08-25 | After | Change |
|---|---|---|---|
| Overnight | ≈ 0 | +13.5 bp | **+14 bp** (t 3.8) |
| Intraday | +10.8 bp | −2.4 bp | **−13 bp** (t −2.8) |
| Close-to-close | — | — | **≈ 0** (not detectable) |

Return moved out of the trading day and into the overnight gap, with no detectable change in the total daily return. The same split holds on one-day nights alone (overnight +13.8 bp, intraday −14.0 bp), so it is not a weekend artifact. It is also not an artifact of "flat" opening prices: the share of opens equal to the prior close barely moves across the break (27% to 26%), and that change can account for only about 0.2 bp of the 14 bp shift. The overnight break survives controls for market trend, volatility and turnover.

Date-stamped: VN-Index overnight-minus-intraday is +4.4 bp pre-COVID (t 1.96), −7.3 bp through the COVID period, and **+21.5 bp from late August 2022 (t 6.1)**.

What we **cannot** claim: we could not pin the break to a single date. Change-point tests put the overnight break anywhere in a wide window spanning roughly 2021–2024, and the intraday break lands around 2022-08-26. The timing coincides with the day HOSE moved to afternoon-of-T+2 sale availability, which is a tempting candidate cause — but we did not test the mechanism, and the interval is too wide to pin it. We report the relocation as a fact and the settlement change as a hypothesis, not a conclusion.

## Finding 3: can you actually capture it? Mostly no

A premium you cannot trade is a curiosity, not an edge. Phase 2 tested the two realistic ways to try.

**Futures (VN30F1M, settle T+0).** This is the one place the overnight trade is literally executable. A strategy that buys every close and sells every open earns a healthy *gross* **+12.9%/yr (t 3.9)** — and then dies on costs, netting about **+1.0%/yr (t 0.45)**, indistinguishable from zero. A narrower **Monday-only** version is more interesting: net 6.4 bp/night (t 2.78) over the full sample. But strip out 2026 and it drops to 3.6 bp (t 1.57) — not significant. It is a *candidate*, not a validated edge, and it is now being tracked forward live with a frozen boundary and a pre-registered kill rule. Zero forward observations so far; a real verdict is years away.

Why do futures capture so little of the index's overnight premium? Because the futures overnight return equals the index overnight return *plus the overnight change in the basis*, and post-2022 the basis systematically narrows during the day — futures under-react to the overnight move and catch up intraday. In 2025 the index earned ~16.7 bp overnight while futures captured ~6.4.

**Stocks under the settlement rule (T+2).** If you buy a basket at the close and hold until you are allowed to sell, the gross return is **+9.0 bp per hold (t 1.30)** — already indistinguishable from zero — and costs turn that into **−21 to −51 bp** depending on the fee assumption. The reason is mechanical: holding through the mandatory T+2 window means you also sit through the intraday legs, which hand back about **79%** of the overnight edge. The equity version is not executable.

**The Phase 2 result, in one line:** the overnight premium is real in the index and the stocks, but the gap between that measured premium and what any instrument can actually keep after costs is large. You can see it; you mostly cannot have it.

## What we could not settle

Stated plainly, because a measurement study is only as honest as its limits:

- **When and why the 2022 regime changed.** The date is not identified and the cause is untested.
- **Whether the Monday futures edge is real.** Zero forward observations; the in-sample case leans heavily on 2026.
- **Pre-2022 futures opens** are unverifiable, and the VN30 index open is degraded in 2019–mid-2021 (which is why the stock basket, not the index, is the reference leg early on).
- **The primary settlement-rule text** (the VSD decision) sits behind a login and was not confirmed against the secondary sources used.

## How it was built, and how to check it

Everything is reproducible and auditable:

- A **point-in-time VN30 reconstruction** (free-float cap weights, 10% cap) validated at 0.9970 correlation to the published index, so the stock tests are free of survivorship and look-ahead bias.
- A **roll-gap repair** that recovered 14 missing futures roll days from per-contract tickers, and an **open-definition audit** that flagged and bounded stale opens — 20–38% of stock-days carry an open equal to the prior close, which, left unhandled, inflates the overnight leg.
- A **claims register**: 31 claims, each with evidence file, confidence interval and status. Where the data forced it, claims were retired — including an earlier "82% of the Monday edge is basis" figure (now undetermined, 48% with a confidence interval from −88% to +138%) and an earlier index-based regime story (re-based on the stock basket once the index open proved unreliable).
- Frozen, hash-verified data snapshots so results reproduce bit-for-bit.

The full methodology, results tables and the claims register are in the repository.

## Takeaways

1. **Vietnam looks developed, not Chinese** — the overnight leg carries the return and is the calmer leg — *but only since about 2022, and partly as a weekend effect over the full sample.*
2. **The headline finding is a relocation, not a windfall.** After 2022, return moved from the intraday session to the overnight gap with no detectable change in the daily total.
3. **You can measure it; you mostly cannot trade it.** Futures capture well under half of it and net to zero after costs; the T+2 equity version loses money.
4. **The interesting open question is "why 2022?"** — a question this study frames but does not answer.

---

*Data via `vnstock` (VCI/KBS). This is a measurement study, not investment advice. Code, data notes and the full claims register: [GitHub repository]. Methodology design doc and progress report included in the repo.*

### References
- French, K. & Roll, R. (1986). *Stock return variances: The arrival of information and the reaction of traders.*
- Lou, D., Polk, C. & Skouras, S. (2019). *A Tug of War: Overnight Versus Intraday Expected Returns.*
- Work on China's T+1 rule and the negative-overnight-return puzzle (e.g. Zhang, 2020).
