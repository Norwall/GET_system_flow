# Локальный инвентарь полных первоисточников

`docs/primary_source_inventory.md` фиксирует полный текст, который был реально
использован для снятия source-gate. Сами PDF, сканы и извлечённый полный текст хранятся локально в
`sources/primary/` и не коммитятся в репозиторий.

## Правила

- Каждая release-запись в `docs/source_gate_manifest.json` должна ссылаться на
  файл из `sources/primary/` через `local_full_text_ref`.
- Для файла обязателен `SHA256`, полная библиографическая ссылка, страницы или
  номера уравнений, дата аудита и решение: `audited_release`,
  `audited_rejected` или `candidate_only`.
- Формулы, коэффициенты, переменные, размерности и область применимости должны
  быть перенесены в `docs/formula_registry.md` до изменения runtime-кода.
- Численные reference-тесты и guard-removal/source-gate тесты должны проходить
  до смены решения manifest на `released`.
- DOI landing page, Crossref/OpenAlex/Unpaywall metadata, abstract, учебник,
  обзор, пересказ формулы или repository landing page без доступного
  full-text/`ORIGINAL` bitstream не являются достаточным основанием для release.

## Инвентарь

На 2026-07-05 локальные полные первоисточники для Checkpoint 5-6 не добавлены.
Все активные Checkpoint 5-6 модели остаются `source_required`.

| Local file | SHA256 | Citation / model | Audited pages/equations | Decision | Notes |
| --- | --- | --- | --- | --- | --- |
| _none_ | _none_ | MSH/Friedel/Zuber-Findlay/WUT/TBD | _none_ | `source_required` | Полный локальный первоисточник ещё не предоставлен. |

## Минимальный release-чеклист

1. Скопировать полный PDF/скан в `sources/primary/`.
2. Посчитать SHA256 локального файла и записать его в таблицу.
3. Выписать страницы, номера уравнений, коэффициенты, convention details и
   область применимости.
4. Обновить `docs/formula_registry.md`,
   `docs/source_audit_checkpoint_5_6.md` и
   `docs/source_gate_manifest.json`.
5. Добавить численные reference-тесты и тест, доказывающий корректное снятие
   guard/source-gate.
6. Только после этого подключать опубликованную модель в runtime.
