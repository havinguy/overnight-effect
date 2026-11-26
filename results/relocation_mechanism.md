# Relocation-mechanism cross-section (why 2022), pre-registered  D=2022-08-25
Members as of 2022-08-01 snapshot; 30 stocks with >= 60 nights each side; window +/-365d.

Pooled mean overnight break: 6.63 bp  (sanity vs basket ~ +13-14 bp)
Pooled mean intraday  break: -10.15 bp
Pooled mean C2C       break: -3.51 bp  (relocation => ~0)

ON break on log(ADV) liquidity:  OLS slope -3.567 bp/unit (t -1.23, n 30); Spearman -0.11
ON break on price:  OLS slope -0.038 bp/unit (t -0.41, n 30); Spearman -0.09
ON break on turnover:  OLS slope +465.940 bp/unit (t +0.46, n 30); Spearman -0.07

Mean break by ADV tercile (bp):
           on_break  id_break  c2c_break
adv_group                               
low-liq        8.47    -11.60      -3.13
mid            6.49     -7.97      -1.48
high-liq       4.94    -10.87      -5.93

ID break on log(ADV): OLS slope +6.344 (t +1.93)
