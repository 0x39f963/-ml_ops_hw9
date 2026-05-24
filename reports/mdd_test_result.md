Generated at: 2026-05-24 17:22:41 MSK

# MDD latency test

- metric: `latency_ms`
- reference rows: `48`
- new rows: `48`
- reference median: `121.00`
- new median: `179.69`
- test: `Mann-Whitney U`, alternative=`greater`
- alpha: `0.05`
- statistic: `2298.000`
- p_value: `0.00000000`
- decision: `add cache before stock history read`

**Вывод:** p-value ниже 0.05, рост latency считаю статистически значимым.
