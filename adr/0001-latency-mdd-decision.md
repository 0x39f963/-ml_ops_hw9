Generated at: 2026-05-24 17:22:41 MSK

# ADR 0001: решение по росту latency прогноза запасов

## Status

Accepted

## Context

Есть два набора измерений latency:

- `data/reference_latency.csv` - нормальная история
- `data/new_latency.csv` - новый вариант расчета

Метрика системная: latency прогноза запасов. Это не accuracy модели, а скорость работы ML-системы.

## Decision

- H0: latency не выросла статистически значимо
- H1: latency выросла статистически значимо
- test: Mann-Whitney U, alternative=`greater`
- alpha: `0.05`
- p-value: `0.00000000`

Decision: добавить cache перед чтением истории остатков + перенести расчет тяжелых lag features в batch preprocessing.

## Consequences

Плюсы:

- меньше p95 latency на inference path
- меньше повторных чтений истории по одному SKU
- проще держать SLO `< 300 ms`

Минусы:

- появляется cache invalidation
- нужен контроль свежести batch features

Что мониторим дальше:

- p95 latency прогноза
- долю stale cache
- MAPE после переноса lag features
