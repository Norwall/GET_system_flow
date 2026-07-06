# Secondary Formula Candidates

Дата: 2026-07-06.

Этот документ фиксирует формулы, найденные в авторитетных вторичных
источниках, когда полный первоисточник пока недоступен. Такие записи помогают
аудиту и будущей реализации, но не снимают `SOURCE_REQUIRED`, не заменяют
локальный intake через `sources/primary/` и не дают права подключать модель как
runtime `published` / `source_complete`.

Статус для всех записей ниже: `SECONDARY_FORMULA_CANDIDATE / NOT_RELEASED`.

## Правило использования

- Вторичная формула может использоваться только как audit guidance.
- Runtime guard остается активным, пока не найден и не аудирован полный
  первоисточник.
- Для release по-прежнему нужны полный текст, SHA256 локального файла,
  страницы/уравнения, convention details, запись в `docs/formula_registry.md`
  и численные reference tests.
- Если вторичный источник противоречит первоисточнику, первоисточник имеет
  приоритет.

## Найденные формульные кандидаты

| Registry ID | Модель | Вторичный источник | Primary record | Решение |
| --- | --- | --- | --- | --- |
| `TP-MULLER-STEINHAGEN-HECK-1986-SECONDARY-CANDIDATE` | Müller-Steinhagen-Heck pressure drop | `fluids.two_phase.Muller_Steinhagen_Heck`, <https://fluids.readthedocs.io/fluids.two_phase.html> | DOI `10.1016/0255-2701(86)80008-3` | Кандидат формулы; `TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE` остается `SOURCE_REQUIRED`. |
| `TP-FRIEDEL-1979-SECONDARY-CANDIDATE` | Friedel pressure drop | `fluids.two_phase.Friedel`, <https://fluids.readthedocs.io/fluids.two_phase.html> | Friedel 1979, European Two-Phase Flow Group Meeting, Ispra, paper E2 | Кандидат формулы; primary paper не найден, gate остается. |
| `VOID-ZIVI-1964-SECONDARY-CANDIDATE` | Zivi slip/void fraction | `fluids.two_phase_voidage.Zivi`, <https://fluids.readthedocs.io/fluids.two_phase_voidage.html> | DOI `10.1115/1.3687113` | Вторичное подтверждение уже реализованной published-записи; не расширяет область применимости. |
| `PRESS-ACCELERATION-ACHP-SECONDARY-CANDIDATE` | Acceleration pressure drop | ACHP FluidCorrelations, <https://achp.sourceforge.net/ACHPComponents/FluidCorrelations.html> | ACHP documentation with cited refrigerant-flow correlations | Кандидат для аудита ускорительного члена; требует той же void fraction, что и hydrostatic/charge balance. |
| `HTC-SHAH-EVAPORATION-SECONDARY-CANDIDATE` | Shah evaporation HTC | ACHP FluidCorrelations, <https://achp.sourceforge.net/ACHPComponents/FluidCorrelations.html> | Shah evaporation correlation cited by ACHP | Кандидат HTC; не является dryout/CHF prediction. |
| `HTC-CHEN-BENNETT-SECONDARY-CANDIDATE` | Chen-Bennett flow-boiling HTC | `ht.boiling_flow.Chen_Bennett`, <https://ht.readthedocs.io/en/release/ht.boiling_flow.html> | Chen/Bennett primary records cited by `ht` | Кандидат HTC; требует wall excess temperature and saturated-flow inputs. |
| `HTC-LIU-WINTERTON-SECONDARY-CANDIDATE` | Liu-Winterton flow-boiling HTC | `ht.boiling_flow.Liu_Winterton`, <https://ht.readthedocs.io/en/release/ht.boiling_flow.html> | Liu and Winterton 1991, cited by `ht` | Кандидат HTC; требует pressure, critical pressure, molecular weight and wall superheat assumptions. |
| `REGIME-TAITEL-DUKLER-1976-HORIZONTAL-SECONDARY-CANDIDATE` | Horizontal / near-horizontal flow pattern map | `fluids.two_phase.Taitel_Dukler_regime`, <https://fluids.readthedocs.io/fluids.two_phase.html> | Taitel and Dukler 1976 horizontal/near-horizontal map | Не заменяет `REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE` for vertical riser. |

## Ненайденные формульные кандидаты

- Wojtan-Ursenbacher-Thome 2005 Part I transition equations and dryout
  boundaries: bibliography and DOI are confirmed, but no auditable secondary
  transcription was found in the current open search.
- Wojtan-Ursenbacher-Thome 2005 Part II heat-transfer/dryout equations:
  bibliography is confirmed, but no auditable secondary formula source was
  found.
- Taitel-Barnea-Dukler 1980 vertical upflow transition equations: DOI and
  abstract are confirmed, but no secondary source with a complete transferable
  equation set was found.
- Kandlikar 1990 and Gungor-Winterton 1986: primary bibliographic records are
  tracked in `docs/source_gate_manifest.json`; no sufficiently clear secondary
  formula transcription was accepted in this pass.

## Candidate-to-release checklist

Before any candidate above can become runtime physics:

1. Obtain the full primary source or a locally auditable scan/PDF.
2. Record file, SHA256, audited pages/equations and release decision in
   `docs/primary_source_inventory.md`.
3. Move exact formulas, definitions, dimensions, conventions and applicability
   into `docs/formula_registry.md`.
4. Add reference-point tests and input-domain rejection tests.
5. Remove runtime guards only in the same change that completes the source
   audit.
