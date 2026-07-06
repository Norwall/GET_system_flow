# Open-web аудит source-gate источников

Дата проверки: 2026-07-05.

Цель проверки - выполнить следующий audit-only проход после `plan.md` и
подтвердить, что ни одна неподтвержденная published-модель не может быть
подключена к runtime без полного первоисточника. Этот документ обновляет
`docs/source_audit_open_web_2026-07-04.md`, но не переносит формулы,
коэффициенты, transition equations, dryout boundaries или HTC-корреляции в код.

Структурированный статус хранится в `docs/source_gate_manifest.json`.

Дополнение от 2026-07-06: отдельный secondary-formula pass оформлен в
`docs/secondary_formula_candidates.md`. Он фиксирует формулы из авторитетных
вторичных источников как `SECONDARY_FORMULA_CANDIDATE / NOT_RELEASED`, но не
меняет результаты endpoint-проверки ниже и не снимает `SOURCE_REQUIRED`.

## Метод проверки

Проверялись только источники, достаточные для возможного снятия source-gate:
publisher PDF/API endpoints, институциональные full-text bitstreams и
официальный OSTI PURL. DOI landing page, Crossref/OpenAlex/Unpaywall metadata,
abstract, учебники, обзоры и пересказы формул по-прежнему считаются только
библиографическим ориентиром.

Локальная проверка endpoints выполнялась Python HTTP-клиентом `urllib.request`
с `HEAD` для publisher/PDF/PURL URLs и `GET` для EPFL DSpace API bundle lists.
PowerShell `Invoke-WebRequest` и `curl.exe` в текущем Windows-окружении
возвращали TLS/Schannel ошибки и не использовались как release-доказательство.

## Результаты endpoint-проверки 2026-07-05

| Модель | Endpoint | Результат | Решение |
| --- | --- | --- | --- |
| Wojtan-Ursenbacher-Thome Part I horizontal map | Elsevier TDM API `PII:S0017931005000268` | HTTP 400 без авторизованного API-контекста; полный текст не получен. | Оставить `REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE` как `SOURCE_REQUIRED`. |
| Wojtan-Ursenbacher-Thome Part I horizontal map | EPFL DSpace bundles для `2c579a38-3bc0-4c50-92a5-f9c345cebe77` | HTTP 200, но bundle list содержит `LICENSE`; `ORIGINAL`/full-text bitstream не найден. | EPFL landing page остаётся `metadata_only`. |
| Taitel-Barnea-Dukler vertical upflow map | Wiley PDF `10.1002/aic.690260304` | HTTP 403 Forbidden. | Оставить `REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE` как `SOURCE_REQUIRED`. |
| Zuber-Findlay drift-flux | ASME PDF `10.1115/1.3689137` | HTTP 403 Forbidden. | Оставить `VOID-ZUBER-FINDLAY-1965-SOURCE-GATE` как `SOURCE_REQUIRED`. |
| Muller-Steinhagen-Heck pressure drop | Elsevier TDM API `PII:0255270186800083` | HTTP 400 без авторизованного API-контекста; полный текст не получен. | Оставить `TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE` как `SOURCE_REQUIRED`. |
| Friedel pressure drop | Primary publisher endpoint | Не идентифицирован; первичная DOI-запись по-прежнему отсутствует в локальном manifest. | Оставить `TP-FRIEDEL-1979-SOURCE-GATE` как `SOURCE_REQUIRED`. |
| Kandlikar 1990 saturated flow boiling | ASME PDF `10.1115/1.2910348` | HTTP 403 Forbidden. | Оставить как `source_required` candidate; не подключать HTC-модель. |
| Gungor-Winterton 1986 flow boiling | Elsevier TDM API `PII:001793108690205X` | HTTP 400 без авторизованного API-контекста; полный текст не получен. | Оставить как `source_required` candidate; не подключать HTC-модель. |
| Wojtan-Ursenbacher-Thome Part II heat-transfer/dryout | Elsevier TDM API `PII:S001793100500027X` | HTTP 400 без авторизованного API-контекста; полный текст не получен. | Оставить как `source_required` candidate; не подключать HTC/dryout-модель. |
| Wojtan-Ursenbacher-Thome Part II heat-transfer/dryout | EPFL DSpace bundles для `32168752-6a94-480e-a56e-8cfd11bb09c1` | HTTP 200, но bundle list содержит `LICENSE`; `ORIGINAL`/full-text bitstream не найден. | EPFL landing page остаётся `metadata_only`. |
| OSTI 1962 saturated convective boiling report | DOI `10.2172/4636495`; `https://www.osti.gov/servlets/purl/4636495` | HTTP 200, `Content-Type: application/pdf`, `Content-Length: 1533908`. | Оставить `source_candidate`: полный текст доступен, но применимость не аудирована. |

## Практическое решение

- Runtime-код не меняется: `published_friction.py` сохраняет guard-функции для
  MSH/Friedel, `published_regimes.py` сохраняет `unknown_or_out_of_range` /
  `source_required`, а `boiling_heat_transfer.py` остаётся diagnostic-only.
- `SOURCE_REQUIRED` не снимается ни для одной записи Checkpoint 5-6.
- Secondary formula candidates после этой проверки используются только как
  audit guidance; они не являются publisher full text, institutional bitstream
  или локальным primary-source intake.
- OSTI 1962 остаётся единственным full-text `source_candidate`, но не заменяет
  Kandlikar/Shah/Gungor-Winterton и не является released-моделью для текущего
  saturated loop solver.
- Следующий достаточный шаг для любого release: получить полный первоисточник,
  занести локальный PDF/скан в некоммитимую папку `sources/primary/`,
  зафиксировать файл, SHA256, страницы/уравнения и audit decision в
  `docs/primary_source_inventory.md`, вручную перенести
  формулы/коэффициенты/переменные/размерности/область применимости в
  `docs/formula_registry.md`, добавить численные reference-тесты и только затем
  удалить соответствующий guard.
