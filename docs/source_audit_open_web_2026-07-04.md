# Open-web аудит source-gate источников

Дата проверки: 2026-07-04.

Цель проверки - найти полные первоисточники для source-gated published-моделей
и кандидатов теплопередачи. Результат этой проверки не переносит формулы в код:
он фиксирует, какие записи имеют только библиографические metadata, какие имеют
закрытые publisher endpoints, и какие могут стать source-candidate после
ручного аудита полного текста.

Структурированный статус хранится в `docs/source_gate_manifest.json`.

## Правило интерпретации

`SOURCE_REQUIRED` нельзя снять по DOI landing page, Crossref metadata, abstract,
OpenAlex/Unpaywall landing page, учебнику, обзору или пересказу. Для release
нужен полный первоисточник: publisher PDF, авторская копия, архивный скан или
институциональный full-text bitstream.

Repository landing page без доступного `ORIGINAL`/full-text bitstream считается
`metadata_only`, даже если Unpaywall/OpenAlex помечают запись как green OA.
EPFL repository landing page без `ORIGINAL`/full-text bitstream не снимает
source-gate.

## Проверенные source-gate записи

| Модель | Первичная запись | Open-web результат | Решение |
| --- | --- | --- | --- |
| Muller-Steinhagen-Heck pressure drop | DOI `10.1016/0255-2701(86)80008-3`; Crossref подтверждает title, journal, pages и Elsevier API endpoints. | Unpaywall/OpenAlex: closed или без repository copy. Elsevier API/TDM endpoint без авторизованного контекста не предоставил полный текст. | Оставить `TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE` как `SOURCE_REQUIRED`. |
| Friedel pressure drop | Friedel 1979, European Two-Phase Flow Group Meeting, Ispra, paper E2. | Crossref title search не дал первичной DOI-записи; publisher/full-text endpoint не найден. | Оставить `TP-FRIEDEL-1979-SOURCE-GATE` как `SOURCE_REQUIRED`. |
| Zuber-Findlay drift-flux | DOI `10.1115/1.3689137`; Crossref подтверждает title, journal, pages и ASME PDF URL. | ASME PDF endpoint вернул `403 Forbidden`; Unpaywall/OpenAlex: closed, без repository copy. | Оставить `VOID-ZUBER-FINDLAY-1965-SOURCE-GATE` как `SOURCE_REQUIRED`. |
| Taitel-Barnea-Dukler vertical map | DOI `10.1002/aic.690260304`; Crossref подтверждает title, journal, pages и Wiley PDF URLs. | Wiley PDF endpoints вернули `403 Forbidden`; Unpaywall/OpenAlex: closed, без repository copy. | Оставить `REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE` как `SOURCE_REQUIRED`. |
| Wojtan-Ursenbacher-Thome Part I horizontal map | DOI `10.1016/j.ijheatmasstransfer.2004.12.012`; Crossref подтверждает title, journal, pages и Elsevier endpoints. | Unpaywall/OpenAlex нашли EPFL green OA landing page, но EPFL DSpace API показал только `LICENSE` bundle и не показал `ORIGINAL`/full-text bitstream. | Оставить `REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE` как `SOURCE_REQUIRED`. |

## Проверенные кандидаты теплопередачи и dryout

| Кандидат | Первичная запись | Open-web результат | Решение |
| --- | --- | --- | --- |
| Kandlikar 1990 saturated flow boiling | DOI `10.1115/1.2910348`; Crossref подтверждает ASME article и PDF URL. | ASME PDF endpoint вернул `403 Forbidden`; Unpaywall: closed, без repository copy. | Не подключать; оставить как source candidate в manifest. |
| Gungor-Winterton 1986 flow boiling | DOI `10.1016/0017-9310(86)90205-x`; Crossref подтверждает Elsevier article и API endpoints. | Unpaywall: closed, без repository copy; Elsevier API endpoint не дал unauthenticated full text. | Не подключать; оставить как source candidate в manifest. |
| Gungor-Winterton 1991 saturated/subcooled extension | DOI `10.1016/0017-9310(91)90234-6`; Crossref подтверждает Elsevier article и API endpoints. | Unpaywall: closed, без repository copy; source-gate не снимается. | Не подключать. |
| Wojtan-Ursenbacher-Thome Part II heat-transfer/dryout | DOI `10.1016/j.ijheatmasstransfer.2004.12.013`; Crossref подтверждает Elsevier article и EPFL landing найден через Unpaywall. | EPFL DSpace API показал только `LICENSE` bundle и не показал `ORIGINAL`/full-text bitstream. | Не подключать; оставить как source candidate в manifest. |
| OSTI 1962 saturated convective boiling report | DOI `10.2172/4636495`; OSTI page содержит full-text PURL. | `https://www.osti.gov/servlets/purl/4636495` вернул `application/pdf`, `Content-Length 1533908`. | Пометить как `source_candidate`, не как released model: применимость к текущей постановке ещё не аудирована. |

## Практическое решение

- Никакие формулы, коэффициенты, transition equations, dryout boundaries или
  HTC-корреляции не переносятся в runtime по результатам этого поиска.
- `published_friction.py` продолжает держать MSH и Friedel за guard-функциями.
- `published_regimes.py` продолжает возвращать `unknown_or_out_of_range` /
  `source_required` для WUT и TBD.
- `boiling_heat_transfer.py` продолжает выдавать diagnostic-only
  `source_required` для HTC/dryout.
- OSTI 1962 является единственным найденным full-text source-candidate, но
  требует отдельного аудита применимости до внесения в `docs/formula_registry.md`
  как реализованной формулы.

## Что считать следующим достаточным шагом

Для снятия любого gate нужно добавить в проект или указать устойчивую ссылку на
полный текст, затем вручную сверить формулы, коэффициенты, переменные,
размерности, область применимости и численные контрольные точки. Только после
этого можно менять `decision` на `released`, обновлять `docs/formula_registry.md`
и подключать код.
