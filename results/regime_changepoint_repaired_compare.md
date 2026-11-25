# Change-point audit: original vs repaired futures input (side-by-side)

Script `src/regime_changepoint_repaired.py` executes `src/regime_changepoint_audit.py` with only the substitutions listed in its header (futures input -> frozen VN30F1M_repaired.csv; output prefix; reproduction gate replaced by recording). Full variant outputs: `results/regime_changepoint_repaired_audit.md` + CSVs. Same seeds; n differs, so bootstrap resamples differ (Monte Carlo SE of p shown).

## Plain split at 2022-08-25 (original gate values vs repaired input)

```
                                              test  t_repaired  t_original
                                         basket ON       3.670       3.766
                                         basket ID      -2.738      -2.619
                                        futures ON       0.446       0.594
paired: break of (basket ON - futures ON) per date       5.018       5.018
```

## 1. Change-point scan

```
          series  n_orig  n_rep ls_date_orig ls_date_rep                ci_orig                 ci_rep  sup_t_orig  sup_t_rep  p_holm_orig  p_holm_rep  mc_se_p_rep  t_cut_orig  t_cut_rep  detected_orig  detected_rep  cut_inside_orig  cut_inside_rep  changes
           CW ON    1559   1572   2022-11-25  2022-11-25 2021-04-09..2024-08-20 2021-03-10..2024-08-21       4.544      4.480        0.012       0.012        0.002       3.766      3.670           True          True             True            True interval
           CW ID    1559   1572   2022-08-26  2022-08-26 2020-06-04..2025-06-18 2020-05-22..2025-06-20       2.658      2.776        0.168       0.108        0.007      -2.619     -2.738          False         False             True            True interval
           EW ON    1559   1572   2022-11-25  2022-11-25 2021-09-01..2024-03-20 2021-10-19..2024-04-17       4.915      4.862        0.012       0.010        0.001       4.099      4.007           True          True             True            True interval
           EW ID    1559   1572   2022-08-26  2022-08-26 2020-12-30..2024-11-20 2020-08-26..2024-08-30       3.560      3.675        0.018       0.018        0.002      -3.517     -3.632           True          True             True            True interval
          FUT ON    1559   1572   2020-03-17  2020-03-17 2020-02-06..2025-06-03 2020-02-11..2025-04-25       2.136      2.074        0.309       0.345        0.015       0.594      0.446          False         False             True            True interval
PAIRED CW-FUT ON    1559   1572   2022-12-07  2022-12-07 2022-03-25..2024-05-29 2021-11-25..2023-12-29       5.770      5.792        0.012       0.006        0.001       5.018      5.018           True          True             True            True interval
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
           CW ON     -0.231    -0.214 NOT DISTINGUISHABLE NOT DISTINGUISHABLE
           EW ON     -0.354    -0.336 NOT DISTINGUISHABLE NOT DISTINGUISHABLE
PAIRED CW-FUT ON      1.138     1.138 NOT DISTINGUISHABLE NOT DISTINGUISHABLE
```

## 5. Monday rows: numerically identical: True (the repaired rows are all after 2022-08-25, outside both Monday windows).

## Summary (5 lines)

1. Sample: n 1559 -> 1572 one-day nights (repaired post-expiry days enter as futures/basket common dates); plain-split t at 08-25 CW ON 3.77 -> 3.67, paired 5.02 -> 5.02.
2. Changes (LS date / interval / detected / Holm crossing 0.05 / cutover inside): CW ON: interval (LS 2022-11-25 -> 2022-11-25; CI 2021-04-09..2024-08-20 -> 2021-03-10..2024-08-21; Holm 0.012 -> 0.012); CW ID: interval (LS 2022-08-26 -> 2022-08-26; CI 2020-06-04..2025-06-18 -> 2020-05-22..2025-06-20; Holm 0.168 -> 0.108); EW ON: interval (LS 2022-11-25 -> 2022-11-25; CI 2021-09-01..2024-03-20 -> 2021-10-19..2024-04-17; Holm 0.012 -> 0.010); EW ID: interval (LS 2022-08-26 -> 2022-08-26; CI 2020-12-30..2024-11-20 -> 2020-08-26..2024-08-30; Holm 0.018 -> 0.018); FUT ON: interval (LS 2020-03-17 -> 2020-03-17; CI 2020-02-06..2025-06-03 -> 2020-02-11..2025-04-25; Holm 0.309 -> 0.345); PAIRED CW-FUT ON: interval (LS 2022-12-07 -> 2022-12-07; CI 2022-03-25..2024-05-29 -> 2021-11-25..2023-12-29; Holm 0.012 -> 0.006).
3. Unchanged series: none; detected set original CW ON, EW ON, EW ID, PAIRED CW-FUT ON vs repaired CW ON, EW ON, EW ID, PAIRED CW-FUT ON.
4. Placebo: CW ON 3->3/10, CW ID 0->0/10, EW ON 3->3/10, EW ID 0->0/10, FUT ON 7->10/10, PAIRED CW-FUT ON 4->4/10; ramp CW ON dAIC -0.23 -> -0.21 (NOT DISTINGUISHABLE -> NOT DISTINGUISHABLE).
5. Monday rows identical: True. Report only; differences are not reinterpreted in this run.
