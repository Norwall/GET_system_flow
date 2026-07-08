# Source audit follow-up 2026-07-06

Этот follow-up фиксирует дополнительную проверку первичных записей после
добавления `source_gate_pipeline.py`. Он не снимает `SOURCE_REQUIRED` gates:
формулы по-прежнему нельзя переносить в runtime без локального полного
первоисточника, SHA256, страниц/уравнений и reference-тестов.

## Проверенные записи

| Модель | Проверенная запись | Результат | Решение |
| --- | --- | --- | --- |
| Muller-Steinhagen-Heck 1986 | Crossref `10.1016/0255-2701(86)80008-3` | Подтверждены Elsevier metadata, pages 297-308, DOI, TDM endpoints и библиография. Full text без авторизованного доступа не получен. | Оставить `SOURCE_REQUIRED`; искать полный Elsevier article или легальный TDM/full-text доступ. |
| Friedel 1979 | Косвенная запись в библиографии MSH 1986 | MSH Crossref reference указывает Friedel, `3R Int.`, volume 18, issue 7, first page 485, 1979, title "Improved friction pressure drop correlations for horizontal and vertical two-phase flow". | Обновить поиск: искать архив `3R International 18(7), 485, 1979`, а не только conference paper E2. |
| Zuber-Findlay 1965 | Crossref `10.1115/1.3689137` | Подтверждены ASME metadata, abstract, pages 453-468 и PDF endpoint. Полный PDF не добавлен локально. | Оставить `SOURCE_REQUIRED`; получить ASME full text и сверить `C0`, weighted drift velocity and averaging definitions. |
| Taitel-Barnea-Dukler 1980 | Crossref `10.1002/aic.690260304` | Подтверждены Wiley metadata, abstract, pages 345-354 и PDF/TDM endpoints. Полный PDF не добавлен локально. | Оставить `SOURCE_REQUIRED`; получить full text и transcribe all vertical transition equations. |
| Wojtan-Ursenbacher-Thome Part I 2005 | Crossref `10.1016/j.ijheatmasstransfer.2004.12.012` | Подтверждены Elsevier metadata, pages 2955-2969, TDM endpoints and references to Kattan 1998, Taitel-Dukler 1976, VDI Heat Atlas and dryout literature. Full text не получен. | Оставить `SOURCE_REQUIRED`; получить Part I full text before published horizontal map implementation. |
| Wojtan-Ursenbacher-Thome Part II 2005 | Crossref `10.1016/j.ijheatmasstransfer.2004.12.013` | Подтверждены Elsevier metadata, pages 2970-2985, TDM endpoints and references to Kattan heat-transfer map, Cooper, Groeneveld and Wojtan PhD thesis. Full text не получен. | Оставить `SOURCE_REQUIRED`; получить Part II full text before dryout/HTC implementation. |
| Chen 1962 OSTI | Local `sources/primary/chen_1962_osti_4636495.pdf` | PDF скачан, SHA256 записан в `docs/primary_source_inventory.md`; pages 4, 6, 10-19 extracted for candidate audit. Key `F` and `S` functions are graphical and require digitizing/reference tests; later hand-calculation arithmetic is recorded in `docs/chen_1962_hand_calculation_2026-07-08.md`. | Оставить `candidate_only`; next step is review/promote the hand calculation and obtain reference-point HTC tests, not runtime release. |

Chen 1962 now has a separate page/equation candidate audit in
`docs/chen_1962_formula_audit_2026-07-06.md`. The audit maps pages 4, 6,
10-19, 20-25 and 32-33 to the additive micro/macro structure, scan-verified
Eqs. (9), (17), (18), applicability limits, nomenclature, tables and graphical
`F/S` functions. The release decision remains `candidate_only` because the
`F/S` curves now have candidate-only digitization in
`docs/chen_1962_graph_digitization_2026-07-07.md`, but release-grade review,
`docs/chen_1962_graph_review_2026-07-08.md` now records a rendered-overlay
review, and candidate SI/graph-axis helpers exist, but release-grade
helper-to-runtime mapping, accepted graph uncertainty and reference HTC tests
have not been released.

## Повторная endpoint-проверка 2026-07-06

- Taitel-Barnea-Dukler 1980: Crossref `10.1002/aic.690260304`
  подтверждает DOI, Wiley/AIChE Journal, pages 345-354, PDF/TDM links,
  41 references and metadata indexed 2026-07-04. Прямой Wiley PDF endpoint
  `https://aiche.onlinelibrary.wiley.com/doi/pdf/10.1002/aic.690260304`
  вернул HTTP 403 Cloudflare challenge, поэтому full text не добавлен
  локально и `SOURCE_REQUIRED` остается.
- Zuber-Findlay 1965: официальный ASME PDF endpoint
  `http://asmedigitalcollection.asme.org/heattransfer/article-pdf/87/4/453/5908192/453_1.pdf`
  переадресует на HTTPS и возвращает HTTP 403 Cloudflare challenge без
  авторизованного контекста. Full text не добавлен локально и gate остается
  `SOURCE_REQUIRED`.

## EPFL dissertation follow-up 2026-07-06

- Wojtan-Ursenbacher-Thome Part I/II journal repository records were checked
  through EPFL DSpace API. The journal items themselves expose
  `datacite.rights=metadata-only` and only a `LICENSE` bundle; they still do
  not expose an `ORIGINAL` full-text bitstream and therefore do not release the
  journal gates.
- EPFL search found candidate `DISS-WOJTAN-2004-EPFL-TH2978`: Leszek Wojtan,
  "Experimental and analytical investigation
  of void fraction and heat transfer during evaporation in horizontal tubes",
  EPFL thesis no. 2978, 2004, repository handle
  `20.500.14299/212227`. The `ORIGINAL` bundle contains openaccess
  `EPFL_TH2978.pdf`, bitstream
  `285f44f3-559e-4d9d-ada4-233895ecd47e`, size 3,070,643 bytes, MD5
  `76a9ee540c12d736399c65753a4d10e2`. Local intake:
  `sources/primary/wojtan_2004_epfl_th2978.pdf`, SHA256
  `0F17826CA107DD8744E8AFA914E11FB422D5BC551589ACE5492B04F5669075D5`,
  decision `candidate_only`.
- EPFL search also found candidate `DISS-MORENO-QUIBEN-2005-EPFL-TH3337`:
  Jesus Moreno Quiben, "Experimental and analytical
  study of two-phase pressure drops during evaporation in horizontal tubes",
  EPFL thesis no. 3337, 2005, repository handle `20.500.14299/215783`.
  The `ORIGINAL` bundle contains openaccess `EPFL_TH3337.pdf`, bitstream
  `005ec5e9-6a5a-49e9-812b-e31d942503b2`, size 3,116,560 bytes, MD5
  `5c39929c145435da6d3e015b6a98ba3e`. Local intake:
  `sources/primary/moreno_quiben_2005_epfl_th3337.pdf`, SHA256
  `B3FD9477D189C7720836C222BFD927BED34AD9E99CB4D1C188102423E26D1A77`,
  decision `candidate_only`.
- These dissertations are now audit candidates for formulas, definitions and
  reference context. They do not release the journal source gates until pages,
  equations, applicability limits and numerical tests are audited and recorded
  explicitly.
- Page-level dissertation evidence is now recorded separately in
  `docs/dissertation_formula_audit_2026-07-06.md`. The Moreno Quiben TH3337
  audit maps pages 20-25, 53-66, 109-125, 146, 149 and 152 to definitions,
  Friedel/MSH candidate formulas, WUT-map segmentation and bibliography. The
  Wojtan TH2978 audit records that the local PDF is available, but its formula
  text layer is partially custom-encoded and requires OCR/manual audit before
  any WUT/HTC release decision; the more specific text-layer blocker is
  recorded in `docs/wojtan_th2978_text_layer_audit_2026-07-08.md`. A later
  rendered-page follow-up in
  `docs/wojtan_th2978_rendered_dryout_audit_2026-07-08.md` locks only
  dryout-limit Eqs. (7.47)-(7.48) as candidate-only evidence; Eq. (7.49), WUT
  map transitions and Part II HTC remain blocked.
- Follow-on dryout-boundary candidate lock is recorded in
  `docs/wojtan_th3337_dryout_boundary_audit_2026-07-07.md`: TH3337 `xdi`/`xde`
  equations are now test-backed by
  `boiling_heat_transfer.wojtan_th3337_candidate_dryout_boundaries`, but they
  remain `candidate_only` and do not release WUT Part I/II, dryout, CHF, or HTC.
- Follow-on annular pressure-drop candidate lock is recorded in
  `docs/moreno_quiben_th3337_annular_pressure_drop_audit_2026-07-07.md`:
  TH3337 Eq. (7.4)/(7.5) is test-backed by
  `published_friction.moreno_quiben_th3337_candidate_annular_pressure_gradient_pa_per_m`,
  but remains `candidate_only` and does not release MSH/Friedel/WUT/HTC gates.
- Follow-on mist pressure-drop candidate lock is recorded in
  `docs/moreno_quiben_th3337_mist_pressure_drop_audit_2026-07-07.md`:
  TH3337 Eq. (7.13)-(7.17) is test-backed by
  `published_friction.moreno_quiben_th3337_candidate_mist_pressure_gradient_pa_per_m`,
  but remains `candidate_only` and does not release MSH/Friedel/WUT/HTC gates.
- Follow-on dryout pressure-drop candidate lock is recorded in
  `docs/moreno_quiben_th3337_dryout_pressure_drop_audit_2026-07-07.md`:
  TH3337 Eq. (7.18) is test-backed by
  `published_friction.moreno_quiben_th3337_candidate_dryout_interpolated_pressure_gradient_pa_per_m`,
  but remains `candidate_only` and does not release MSH/Friedel/WUT/HTC gates.
- Follow-on slug/intermittent pressure-drop candidate lock is recorded in
  `docs/moreno_quiben_th3337_slug_pressure_drop_audit_2026-07-07.md`:
  TH3337 Eq. (7.6)/(7.12) is test-backed by
  `published_friction.moreno_quiben_th3337_candidate_slug_interpolated_pressure_gradient_pa_per_m`,
  but remains `candidate_only` and does not release MSH/Friedel/WUT/HTC gates.
- Follow-on stratified-wavy pressure-drop candidate lock is recorded in
  `docs/moreno_quiben_th3337_stratified_wavy_pressure_drop_audit_2026-07-08.md`:
  TH3337 Eq. (7.9)-(7.11) is test-backed by
  `published_friction.moreno_quiben_th3337_candidate_stratified_wavy_pressure_gradient_pa_per_m`,
  but remains `candidate_only` and does not release MSH/Friedel/WUT/HTC gates.

## Новые действия в pipeline

- `python -m source_gate_pipeline --pretty` теперь отдаёт summary,
  source-gate records, primary URLs, audit checks, tests, staged action
  pipeline and next priorities.
- `/api/source-gates` возвращает тот же report для локального designer/API.
- Первым приоритетом является `HTC-CHEN-1962-SOURCE-CANDIDATE`, потому что
  локальный полный текст уже доступен. Его release всё равно требует переноса
  уравнений, reviewed digitized `F/S` functions, области применимости и численных
  reference-тестов.
