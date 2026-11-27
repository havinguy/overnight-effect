# Change-point audit: original vs repaired futures input (side-by-side)

Script `src/regime_changepoint_repaired.py` executes `src/regime_changepoint_audit.py` with only the substitutions listed in its header (futures input -> frozen VN30F1M_repaired.csv; output prefix; reproduction gate replaced by recording). Full variant outputs: `results/regime_changepoint_repaired_audit.md` + CSVs. Same seeds; n differs, so bootstrap resamples differ (Monte Carlo SE of p shown).

## Plain split at 2022-08-25 (original gate values vs repaired input)

```
                                              test  t_repaired  t_original
                                         basket ON       3.714       3.810
                                         basket ID      -2.782      -2.663
                                        futures ON       0.480       0.628
paired: break of (basket ON - futures ON) per date       5.051       5.050
```

## 1. Change-point scan

```
          series  n_orig  n_rep ls_date_orig ls_date_rep                ci_orig                 ci_rep  sup_t_orig  sup_t_rep  p_holm_orig  p_holm_rep  mc_se_p_rep  t_cut_orig  t_cut_rep  detected_orig  detected_rep  cut_inside_orig  cut_inside_rep  changes
           CW ON    1560   1573   2022-11-25  2022-11-25 2021-06-18..2024-10-01 2021-06-30..2024-10-29       4.586      4.522        0.012       0.012        0.002       3.810      3.714           True          True             True            True interval
           CW ID    1560   1573   2022-08-26  2022-08-26 2020-05-28..2025-05-29 2020-05-21..2025-03-19       2.702      2.820        0.166       0.106        0.007      -2.663     -2.782          False         False             True            True interval
           EW ON    1560   1573   2022-11-25  2022-11-25 2021-08-10..2024-02-20 2021-11-10..2024-03-19       4.960      4.907        0.012       0.006        0.001       4.145      4.053           True          True             True            True interval
           EW ID    1560   1573   2022-08-26  2022-08-26 2021-01-12..2024-08-21 2020-11-17..2024-08-28       3.610      3.725        0.015       0.012        0.002      -3.567     -3.683           True          True             True            True interval
          FUT ON    1560   1573   2020-03-17  2020-03-17 2020-02-05..2025-04-17 2020-02-07..2025-04-24       2.195      2.134        0.262       0.327        0.015       0.628      0.480          False         False             True            True interval
PAIRED CW-FUT ON    1560   1573   2022-12-07  2022-12-07 2022-03-31..2024-02-29 2021-12-08..2023-12-19       5.802      5.824        0.012       0.006        0.001       5.050      5.051           True          True             True            True interval
```

## 2. Placebo ranking (random dates with |t_window| above 08-25)

```
          series  random_above_orig  random_above_rep  t_cut_window_orig  t_cut_window_rep  same_random_dates
           CW ON                  3                 3              1.247             1.122               True
           CW ID                  0                 0             -1.692            -1.556               True
           EW ON                  3                 3              1.419             1.266               True
           EW ID                  0                 0             -2.024            -1.855               True
          FUT ON                  7                10              0.444             0.141               True
PAIRED CW-FUT ON                  4                 4              1.453             1.496               True
```

## 3. Ramp vs step

```
          series  dAIC_orig  dAIC_rep        verdict_orig         verdict_rep
           CW ON     -0.237    -0.221 NOT DISTINGUISHABLE NOT DISTINGUISHABLE
           EW ON     -0.363    -0.344 NOT DISTINGUISHABLE NOT DISTINGUISHABLE
PAIRED CW-FUT ON      1.139     1.139 NOT DISTINGUISHABLE NOT DISTINGUISHABLE
```

## 5. Monday rows: numerically identical: True (the repaired rows are all after 2022-08-25, outside both Monday windows).

## Summary (5 lines)

1. Sample: n 1560 -> 1573 one-day nights (repaired post-expiry days enter as futures/basket common dates); plain-split t at 08-25 CW ON 3.81 -> 3.71, paired 5.05 -> 5.05.
2. Changes (LS date / interval / detected / Holm crossing 0.05 / cutover inside): CW ON: interval (LS 2022-11-25 -> 2022-11-25; CI 2021-06-18..2024-10-01 -> 2021-06-30..2024-10-29; Holm 0.012 -> 0.012); CW ID: interval (LS 2022-08-26 -> 2022-08-26; CI 2020-05-28..2025-05-29 -> 2020-05-21..2025-03-19; Holm 0.166 -> 0.106); EW ON: interval (LS 2022-11-25 -> 2022-11-25; CI 2021-08-10..2024-02-20 -> 2021-11-10..2024-03-19; Holm 0.012 -> 0.006); EW ID: interval (LS 2022-08-26 -> 2022-08-26; CI 2021-01-12..2024-08-21 -> 2020-11-17..2024-08-28; Holm 0.015 -> 0.012); FUT ON: interval (LS 2020-03-17 -> 2020-03-17; CI 2020-02-05..2025-04-17 -> 2020-02-07..2025-04-24; Holm 0.262 -> 0.327); PAIRED CW-FUT ON: interval (LS 2022-12-07 -> 2022-12-07; CI 2022-03-31..2024-02-29 -> 2021-12-08..2023-12-19; Holm 0.012 -> 0.006).
3. Unchanged series: none; detected set original CW ON, EW ON, EW ID, PAIRED CW-FUT ON vs repaired CW ON, EW ON, EW ID, PAIRED CW-FUT ON.
4. Placebo: CW ON 3->3/10, CW ID 0->0/10, EW ON 3->3/10, EW ID 0->0/10, FUT ON 7->10/10, PAIRED CW-FUT ON 4->4/10; ramp CW ON dAIC -0.24 -> -0.22 (NOT DISTINGUISHABLE -> NOT DISTINGUISHABLE).
5. Monday rows identical: True. Report only; differences are not reinterpreted in this run.
