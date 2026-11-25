# The Overnight Effect on the Vietnamese Stock Market — Project Design & Methodology

Nov 17, 2026 · @Harry

## Overview

This project tests whether the **overnight effect** — the pattern documented in developed markets where the close-to-open ("overnight") return is systematically positive while the open-to-close ("intraday") return is flat or negative — holds on the Vietnamese stock market, or whether Vietnam's settlement rules and market structure produce a different, possibly reversed, pattern.

Phase 1 decomposes daily close-to-close returns on HOSE into their overnight and intraday components and compares the two legs on both raw and risk-adjusted terms. It is a **measurement study**: it establishes whether the pattern exists in the data, not whether it can be traded. Tradability under Vietnam's T+2 settlement is a separate question, deferred to Phase 2.

## Research question and hypotheses

**Primary question.** When a daily return on HOSE is split into its overnight leg (close → next open) and its intraday leg (open → same-day close), does the overnight leg carry a systematically higher return than the intraday leg, as in developed markets — and does that still hold after adjusting for the risk (volatility) of each leg?

We do not assume a direction. Developed markets show a positive-overnight / negative-intraday split; China, which like Vietnam restricts same-day selling, shows the reverse (negative overnight). Vietnam's sign is an open empirical question, which is what makes the test worth running.

Testable hypotheses:

1. **H1 (raw):** mean overnight return > mean intraday return.
2. **H2 (risk-adjusted):** overnight Sharpe-like ratio (mean / SD) > intraday ratio. This is the stronger claim, and the one that separates a genuine anomaly from mere compensation for overnight risk.
3. **H1-alt (China analog):** given T+2 settlement, the overnight leg may be ≤ 0, reversing the developed-market pattern.
4. **H3 (persistence, Level B):** at the individual-stock level, a stock's past overnight returns predict its future overnight returns, with reversal against the intraday leg.
5. **H4 (tradability, Level C / Phase 2):** any measured edge does not survive realistic transaction costs.

## Background and prior evidence

The split between overnight and intraday returns was first documented by French and Roll (1986). The central modern reference is [Lou, Polk and Skouras (2019), "A Tug of War"](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf), which shows that across 14 well-known strategies, profits accrue almost entirely in one leg or the other, and that individual stocks' overnight and intraday patterns persist for years with an offsetting reversal across the two periods. Broader evidence finds the overnight leg [beating the intraday leg in all 23 countries](https://cxoadvisory.com/calendar-effects/overnight-momentum-informed-overnight-trading) of the MSCI World (developed) index — a sample that does **not** include Vietnam.

The key counterexample is China. Chinese overnight returns are on average negative, which researchers attribute to the [T+1 rule barring same-day sales](https://core.ac.uk/works/67743167); the induced discount on the open is estimated at about 14 basis points, and T+0 venues (Hong Kong stocks, Chinese index futures) show overnight returns near zero instead. Because Vietnam also restricts same-day selling, the Chinese result — not the US one — may be the better prior for what we find.

## Vietnam market structure and constraints

Five features of HOSE shape the design. Two help (clean auction endpoints), three constrain.

| Feature | Detail | Implication for this study |
| --- | --- | --- |
| Open / close mechanism | ATO call auction 09:00–09:15 sets the open; ATC call auction 14:30–14:45 sets the close | Both endpoints are auction-clearing prices — arguably cleaner than continuous-market opens used in some US studies |
| Settlement | T+2; shares not sellable the same day (exact intraday timing of T+2 availability to be verified) | Blocks the literal buy-close / sell-open trade → Phase 1 is measurement only |
| Price limits | ±7% band from the reference price (stocks) | Limit-locked opens or closes censor the split; flag and exclude. Near-absent at the index level |
| Lunch break | 11:30–13:00 trading halt | The intraday leg contains an internal gap; note it, but minor at daily frequency |
| Investor base | Retail-dominated | Opening prices may be sentiment-driven — relevant to interpreting a large or volatile overnight leg |
| Futures | VN30F1M front-month futures trade T+0 | The one instrument where the overnight trade is executable (Level C / Phase 2) |

## Data requirements

Daily OHLC is sufficient for the full decomposition — no intraday tick data is needed for Levels A and B.

Required series:

- **Index:** daily open, high, low, close for the VN-Index and VN30, full available history.
- **Constituents (Level B):** daily OHLC for individual HOSE stocks (VN30 members at minimum, ideally all liquid names), with listing / delisting dates to avoid survivorship bias.
- **Futures (Level C):** daily OHLC for front-month VN30 futures (VN30F1M, listed Aug 2017), with contract and roll dates. Front month only — longer-dated contracts are illiquid.
- **Corporate actions:** ex-dividend and ex-rights dates plus adjustment factors for every stock, so the overnight leg is not polluted by ex-date price drops.
- **Reference / limit data:** daily reference price, to flag ±7% limit hits, where the source provides it.

Open items to confirm with the data source:

1. Source itself — the VN25 pipeline vs. a vendor (vnstock / FiinX / TCBS).
2. How the source defines the "open" when a stock has no ATO match.
3. Whether prices are already corporate-action-adjusted — if so, the raw overnight gap must be recomputed from unadjusted prices or the adjustment handled explicitly.

## Methodology: return decomposition and per-leg statistics

Work in log returns so the two legs add exactly to the daily return. For trading day T with open O and close C:

```latex
r^{\text{overnight}}_T = \ln O_T - \ln C_{T-1} \\
r^{\text{intraday}}_T = \ln C_T - \ln O_T \\
r^{\text{c2c}}_T = r^{\text{overnight}}_T + r^{\text{intraday}}_T
```

For each leg, across the sample, compute and compare:

- **Mean** — the raw edge; annualized × 252.
- **Standard deviation** — the risk of the leg; annualized × √252.
- **Sharpe-like ratio** = mean / SD, annualized. This is the decisive statistic: it answers whether the overnight leg earns more *per unit of risk*, not just more in total.
- **t-statistic** on each leg's mean, and on the mean difference (overnight − intraday), to test significance.
- **Share of positive days** per leg, and the cumulative compounded path of each leg, to show the drift visually.

Report all of the above for the full sample and for sub-periods (see robustness). **Do not compare the legs on mean alone:** they cover different clock spans (overnight ≈ 17.5h plus weekends; intraday ≈ 5h with a lunch break) and typically have very different volatilities, so a raw-mean comparison is not risk-fair. The per-leg SD and Sharpe are what make it one.

&#91;embedded content: the two legs of one daily return\]

The hypothesis concerns whether the solid (overnight) segments carry the positive return while the dashed (intraday) segment is flat or negative.

## Methodology: three analysis levels

Run the decomposition at three levels, each handling Vietnam's constraints differently.

**Level A — Index decomposition (start here).** Apply the split to the VN-Index and VN30. Establishes whether the raw pattern exists at all. Naturally robust to price limits — the index essentially never moves ±7% in a day — and requires no tradability assumption.

**Level B — Cross-sectional single stocks.** Each month, sort stocks on trailing overnight return and test whether high-overnight stocks keep high overnight / low intraday returns (H3). This is the Lou–Polk–Skouras test, and where a Vietnam-specific cross-sectional story — or a China-style negative overnight — would surface. Requires the full cleaning in the next section.

**Level C — VN30 futures (tradability).** Repeat on front-month VN30 futures, which trade T+0, net of realistic costs. Answers whether the effect survives in a genuinely tradable instrument. Caveats: short history (listed Aug 2017), index-only (no cross-section), and the futures basis and roll must be handled. This leg overlaps Phase 2.

## Data cleaning and robustness

These steps are what make the test valid for Vietnam; skipping them produces fake results.

- **Corporate-action adjustment.** Adjust the overnight leg across ex-dividend and ex-rights dates — an unadjusted ex-date looks like a spurious negative overnight return.
- **Price-limit censoring.** Flag any day where the open or close sits within one tick of the ±7% band. Report results with and without limit days; for stocks limit-locked across consecutive sessions, drop the whole locked run.
- **ATO liquidity filter.** Exclude stock-days with no opening-auction match — a missing open is not a zero return. Set a minimum traded-value threshold for Level B inclusion.
- **Log returns** throughout, so the legs sum to the daily return.
- **Outliers.** Winsorize or flag extreme single-day returns; inspect rather than blindly trim.
- **Sub-period splits.** At minimum pre / post-COVID and pre / post the KRX trading-system migration — microstructure changed, and the pattern may not be stationary.
- **Robustness.** Equal- vs value-weighted index construction; sensitivity to the exact open / close definition; Newey–West or bootstrap standard errors for the mean tests.

## Interpreting the outcomes

The result is informative whichever way it comes out.

- **Positive overnight, flat / negative intraday, and overnight Sharpe > intraday Sharpe** — Vietnam behaves like developed markets; the anomaly generalizes to a frontier, retail-driven market. Strongest version of the thesis.
- **Positive overnight on raw means, but overnight Sharpe ≤ intraday Sharpe** — the overnight "edge" is mostly compensation for higher overnight-gap risk, not a free lunch. This is exactly the distinction H2 is built to catch, and the reason per-leg volatility is in the design.
- **Negative overnight (China analog)** — T+2 settlement dominates and Vietnam looks like China, not the US. A clean, publishable finding in its own right, and the more interesting outcome given the prior.
- **No significant difference** — the daily return is not meaningfully clientele-split in Vietnam; worth reporting as a null against a literature that assumes the split is universal.

In every case, report the Vietnam-specific sub-question directly: **is the overnight leg more or less volatile than the intraday leg?** The developed-market "overnight is calmer" result may not hold in a thin, retail-driven market where global news (the US session) lands on the ATO open.

## Scope and phased roadmap

**Phase 1 (this project) — measurement.** Levels A and B on spot data. Decompose, compute per-leg statistics, test H1–H3. No trading assumption; T+2 is irrelevant because nothing is traded. Deliverable: the decomposition results and the statistical comparison.

**Phase 2 (later) — executability.** The T+2-constrained question (what a settlement-bound trader actually captures), Level C on VN30 futures, and a net-of-cost backtest (H4). Kept separate so a contaminated "hold-until-settlement" return never mixes into the clean Phase 1 measurement.

Immediate next steps:

1. Lock the data source and pull daily OHLC for the VN-Index and VN30 (Level A).
2. Confirm corporate-action handling and the open-price definition with the source.
3. Build the decomposition engine (log returns; per-leg mean / SD / Sharpe / t-stats) and run Level A.
4. Review Level A, then scope Level B (which stock universe).

### Sources

- [Lou, Polk & Skouras (2019), *A Tug of War*](https://personal.lse.ac.uk/polk/research/TugOfWar.pdf)
- [Overnight effect across 23 countries (CXO summary)](https://cxoadvisory.com/calendar-effects/overnight-momentum-informed-overnight-trading)
- [The overnight return puzzle and the T+1 rule in China](https://core.ac.uk/works/67743167)
- [Zhang (2020), T+1 trading mechanism causes negative overnight return](https://ideas.repec.org/a/eee/ecmode/v89y2020icp55-71.html)
- [HOSE trading regulations (Vietstock)](https://static2.vietstock.vn/vietstock/2025/4/29/20250429_20250429___hose___trading_regulations_on_hose.pdf)
