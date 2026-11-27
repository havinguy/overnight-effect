# Market-state control audit

Read-only. Script `src/regime_market_state_audit.py`; rules pre-registered in its header before the first run. Futures input: frozen VN30F1M (original), as regime_changepoint_audit.

Sample: 1560 one-day nights; 0 dropped for missing controls -> n 1560 (2018-11-21..2026-11-17). Controls (VNINDEX, known at t-1 close): R60, R120 trailing log returns; RV20 trailing 20-day realized vol; TO = ln(20d / 250d mean volume). z-scored. OLS, NW lag 5.

## Collinearity of POST with the controls

```
      spec  r2_post_on_controls  low_power
A all four                 0.11      False
B R60+R120                 0.00      False
 C RV20+TO                 0.06      False
```

## 1. Break b at 2022-08-25, baseline vs controlled (bp; NW t)

```
          series       spec    n  b_base_bp  t_base  b_ctrl_bp  t_ctrl  retained_share          verdict  low_power_spec
           CW ON A all four 1560      14.28    3.81      14.73    4.19            1.03         SURVIVES           False
           CW ON B R60+R120 1560      14.28    3.81      14.04    3.93            0.98         SURVIVES           False
           CW ON  C RV20+TO 1560      14.28    3.81      17.09    4.71            1.20         SURVIVES           False
           CW ID A all four 1560     -13.30   -2.66      -8.36   -1.65            0.63 ATTENUATED, N.S.           False
           CW ID B R60+R120 1560     -13.30   -2.66     -12.63   -2.53            0.95         SURVIVES           False
           CW ID  C RV20+TO 1560     -13.30   -2.66     -12.79   -2.72            0.96         SURVIVES           False
           EW ON A all four 1560      16.05    4.14      16.28    4.55            1.01         SURVIVES           False
           EW ON B R60+R120 1560      16.05    4.14      15.71    4.28            0.98         SURVIVES           False
           EW ON  C RV20+TO 1560      16.05    4.14      19.04    5.16            1.19         SURVIVES           False
           EW ID A all four 1560     -17.38   -3.57     -13.09   -2.67            0.75         SURVIVES           False
           EW ID B R60+R120 1560     -17.38   -3.57     -16.57   -3.42            0.95         SURVIVES           False
           EW ID  C RV20+TO 1560     -17.38   -3.57     -17.75   -3.91            1.02         SURVIVES           False
          FUT ON A all four 1560       1.64    0.63       3.16    1.31            1.92 ATTENUATED, N.S.           False
          FUT ON B R60+R120 1560       1.64    0.63       1.84    0.71            1.12 ATTENUATED, N.S.           False
          FUT ON  C RV20+TO 1560       1.64    0.63       2.30    0.94            1.40 ATTENUATED, N.S.           False
PAIRED CW-FUT ON A all four 1560      12.64    5.05      11.57    5.05            0.92         SURVIVES           False
PAIRED CW-FUT ON B R60+R120 1560      12.64    5.05      12.20    5.56            0.97         SURVIVES           False
PAIRED CW-FUT ON  C RV20+TO 1560      12.64    5.05      14.79    6.12            1.17         SURVIVES           False
```

Control coefficients (bp per 1 SD, NW t), spec A:

```
          series  c_R60_bp_per_sd  c_R120_bp_per_sd  c_RV20_bp_per_sd  c_TO_bp_per_sd  t_R60  t_R120  t_RV20  t_TO
           CW ON             4.56              3.20              0.18            1.33   1.26    1.53    0.09  0.42
           CW ID           -12.67              0.05              5.57            8.29  -2.88    0.01    1.53  2.50
           EW ON             6.20              2.45              0.18            1.10   1.65    1.12    0.09  0.34
           EW ID           -14.07              1.17              5.96            6.79  -3.22    0.32    1.65  2.09
          FUT ON            -3.18              1.05              2.55            2.59  -1.19    0.62    1.60  1.16
PAIRED CW-FUT ON             7.73              2.15             -2.37           -1.26   3.25    1.61   -1.71 -0.58
```

- Spec A: CW ON +14.28 -> +14.73 bp (t 3.81 -> 4.19) SURVIVES; CW ID -13.30 -> -8.36 bp (t -2.66 -> -1.65) ATTENUATED, N.S.. Answer under the rule: break does NOT survive (both legs required) market-state control.

## 2. Drawdown episodes (VNINDEX trough; ±125 one-day nights)

```
 episode     trough        series                status                 window contains_cutover  drawdown_pct  dON_bp  tON  dID_bp   tID  dC2C_bp  tC2C signature                                     role
    2018 2018-10-30 VNINDEX (VCI)                    ok 2018-03-15..2019-06-20            False        -26.21   11.23 1.81   -0.43 -0.04    10.79  0.82     False                                  placebo
    2018 2018-10-30     CW basket window outside sample                    NaN              NaN           NaN     NaN  NaN     NaN   NaN      NaN   NaN       NaN                                      NaN
    2020 2020-03-24 VNINDEX (VCI)                    ok 2019-08-02..2020-11-05            False        -35.68   20.84 1.84   11.11  1.16    31.95  2.40     False                                  placebo
    2020 2020-03-24     CW basket                    ok 2019-08-02..2020-11-05            False        -35.68   22.80 1.77    3.01  0.27    25.81  2.02     False                                  placebo
    2022 2022-11-15 VNINDEX (VCI)                    ok 2022-03-31..2023-07-05             True        -40.34   22.70 2.79   -5.74 -0.38    16.96  1.21     False comparator (same episode as the cutover)
    2022 2022-11-15     CW basket                    ok 2022-03-31..2023-07-18             True        -40.34   20.00 2.32   -0.63 -0.04    19.37  1.27     False comparator (same episode as the cutover)
```

Caveat: VNINDEX legs use VCI opens (flagged opens kept); the 2018 episode has no basket data (sample starts 2018-11-21) and no KBS cross-check.

Integrity: md5 of every pre-existing file in data/raw/ and results/ identical before and after: True (254 files).

## Summary (5 lines)

1. Collinearity: R^2 of POST on controls A 0.11, B 0.00, C 0.06 (none flagged LOW POWER); n 1560.
2. Spec A (all four controls): CW ON b +14.3 -> +14.7 bp, t 3.81 -> 4.19 (SURVIVES); CW ID -13.3 -> -8.4, t -2.66 -> -1.65 (ATTENUATED, N.S.) -> break does not survive under the rule.
3. Other series, spec A: EW ON t 4.14 -> 4.55 (SURVIVES); EW ID t -3.57 -> -2.67 (SURVIVES); FUT ON t 0.63 -> 1.31 (ATTENUATED, N.S.); PAIRED CW-FUT ON t 5.05 -> 5.05 (SURVIVES). Specs B/C in the table.
4. Placebo drawdowns (VNINDEX legs): 2018 VNINDEX (VCI) dON +11.2 (t 1.81), dID -0.4 (t -0.04), dC2C +10.8 (t 0.82) -> no signature; 2020 VNINDEX (VCI) dON +20.8 (t 1.84), dID +11.1 (t 1.16), dC2C +32.0 (t 2.40) -> no signature; basket 2020 CW basket dON +22.8 (t 1.77), dID +3.0 (t 0.27), dC2C +25.8 (t 2.02) -> no signature.
5. Comparator 2022 trough window (contains the cutover): 2022 VNINDEX (VCI) dON +22.7 (t 2.79), dID -5.7 (t -0.38), dC2C +17.0 (t 1.21) -> no signature; basket 2022 CW basket dON +20.0 (t 2.32), dID -0.6 (t -0.04), dC2C +19.4 (t 1.27) -> no signature. Report only, no reinterpretation.
