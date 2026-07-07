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

На 2026-07-06 локально добавлены полный OSTI PDF для Chen 1962 и два
openaccess EPFL doctoral-thesis PDF как `candidate_only`: это подтверждает
наличие полных текстов для дальнейшего аудита, но не выпускает runtime
HTC/pressure-drop/regime-корреляции. Все активные Checkpoint 5-6 журнальные
модели остаются `source_required`.

| Local file | SHA256 | Citation / model | Audited pages/equations | Decision | Notes |
| --- | --- | --- | --- | --- | --- |
| _none_ | _none_ | MSH/Friedel/Zuber-Findlay/WUT/TBD | _none_ | `source_required` | Полный локальный первоисточник ещё не предоставлен. |
| `sources/primary/chen_1962_osti_4636495.pdf` | `5DDE91B1FE38B2CE6E4977AEE2A25A61BBEDC83C5A7214802496754E4989017E` | `HTC-OSTI-1962-SOURCE-CANDIDATE`; J. C. Chen, "A correlation for boiling heat transfer to saturated fluids in convective flow", OSTI ID 4636495, DOI `10.2172/4636495` | Pages 4, 6, 10-19, 20-25, 32-33 reviewed in `docs/chen_1962_formula_audit_2026-07-06.md`; confirms additive micro/macro structure, Eq. (9)/(17)/(18) release targets, applicability conditions, graphical `F`/`S` functions and quality limits. | `candidate_only` | Full text is locally available for audit, but the key `F` and `S` functions are graphical, OCR is degraded around several formulas, and no runtime reference-point tests have been released. |
| `sources/primary/wojtan_2004_epfl_th2978.pdf` | `0F17826CA107DD8744E8AFA914E11FB422D5BC551589ACE5492B04F5669075D5` | `DISS-WOJTAN-2004-EPFL-TH2978`; Leszek Wojtan, "Experimental and analytical investigation of void fraction and heat transfer during evaporation in horizontal tubes", EPFL thesis no. 2978, 2004, openaccess ORIGINAL bitstream `EPFL_TH2978.pdf` | Pages 1, 9-13, 172-183 reviewed in `docs/dissertation_formula_audit_2026-07-06.md`; title page is readable, but the equation text layer is partially custom-encoded and requires OCR/manual audit. | `candidate_only` | Dissertation full text is locally available for audit guidance for void fraction, horizontal evaporation HTC, and Wojtan/Thome context; it does not release WUT journal gates without page/equation audit and reference tests. |
| `sources/primary/moreno_quiben_2005_epfl_th3337.pdf` | `B3FD9477D189C7720836C222BFD927BED34AD9E99CB4D1C188102423E26D1A77` | `DISS-MORENO-QUIBEN-2005-EPFL-TH3337`; Jesus Moreno Quiben, "Experimental and analytical study of two-phase pressure drops during evaporation in horizontal tubes", EPFL thesis no. 3337, 2005, openaccess ORIGINAL bitstream `EPFL_TH3337.pdf` | Pages 1, 5, 20-25, 53-66, 109-125, 146, 149, 152 reviewed in `docs/dissertation_formula_audit_2026-07-06.md`; confirms definitions, Friedel/MSH candidate formulas, WUT-map segmentation, and bibliography links. | `candidate_only` | Dissertation full text is locally available for pressure-drop audit guidance, including Friedel and Muller-Steinhagen-Heck context; it does not release friction gates without primary article audit or dissertation-specific formula release decision and tests. |

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
