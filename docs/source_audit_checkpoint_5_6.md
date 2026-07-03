# Аудит источников Checkpoint 5-6

Дата проверки: 2026-07-03.

Цель проверки - отделить библиографически подтвержденные published-модели от
формул, которые можно переносить в расчет только после сверки полного
первоисточника. Этот документ является академическим ограничителем: наличие DOI
или landing page не считается достаточным основанием для переноса коэффициентов,
transition equations или областей применимости в код.

## Подтвержденные библиографические записи

| Модель | Первичная запись | Статус доступа |
| --- | --- | --- |
| Muller-Steinhagen-Heck pressure drop | H. Muller-Steinhagen, K. Heck. A simple friction pressure drop correlation for two-phase flow in pipes. Chemical Engineering and Processing, 1986, 20(6), 297-308. DOI `10.1016/0255-2701(86)80008-3`. | Crossref подтверждает DOI, страницы и Elsevier landing/TDM endpoints. Полный текст через проверенный endpoint без авторизованного API-контекста не получен. |
| Friedel pressure drop | L. Friedel. Improved friction pressure drop correlations for horizontal and vertical two-phase flow. European Two-Phase Flow Group Meeting, Ispra, paper E2, 1979. | Первичная DOI-запись в Crossref по названию не найдена. Оставлено как `SOURCE_REQUIRED`. |
| Zuber-Findlay drift-flux | N. Zuber, J. A. Findlay. Average Volumetric Concentration in Two-Phase Flow Systems. Journal of Heat Transfer, 1965, 87(4), 453-468. DOI `10.1115/1.3689137`. | Crossref подтверждает DOI, страницы и ASME PDF URL. Прямой HEAD-запрос к PDF вернул `403 Forbidden`, поэтому коэффициенты не перенесены. |
| Taitel-Barnea-Dukler vertical upflow map | Y. Taitel, D. Barnea, A. E. Dukler. Modelling flow pattern transitions for steady upward gas-liquid flow in vertical tubes. AIChE Journal, 1980, 26(3), 345-354. DOI `10.1002/aic.690260304`. | Crossref подтверждает DOI, страницы и Wiley PDF URL. Прямой HEAD-запрос к PDF вернул `403 Forbidden`, поэтому transition equations не перенесены. |
| Wojtan-Ursenbacher-Thome horizontal boiling map | L. Wojtan, T. Ursenbacher, J. R. Thome. Investigation of flow boiling in horizontal tubes: Part I - A new diabatic two-phase flow pattern map. International Journal of Heat and Mass Transfer, 2005, 48, 2955-2969. DOI `10.1016/j.ijheatmasstransfer.2004.12.012`. | Crossref подтверждает DOI, страницы и Elsevier landing/TDM endpoints. Полный текст через проверенный endpoint без авторизованного API-контекста не получен. |

## Решение для кода

- `published_regimes.py` остается source-gated: горизонтальная WUT-карта и
  вертикальная TBD-карта возвращают `unknown_or_out_of_range` со статусом
  `source_required`.
- `published_friction.py` оставляет MSH и Friedel как функции-заглушки,
  выбрасывающие `SourceRequiredCorrelationError`.
- Zuber-Findlay пока не добавляется как расчетная drift-flux ветка; текущие
  коэффициенты `C0/Kd` остаются только в experimental-слое.
- Новый вход `regime_model` отделяет режимную диагностику от `closure_model`.
  Значение `published_regime_map` означает source-gated published metadata, а
  `experimental_regime_aware` - старые эвристические пороги.

## Что нужно для снятия source-gate

- Локальный или институционально доступный полный текст первоисточника.
- Переписанные в `docs/formula_registry.md` формулы, коэффициенты, переменные,
  размерности и область применимости.
- Тесты на численные контрольные точки и граничные режимы.
- Проверка соглашений Darcy/Fanning, полного или фазового массового потока,
  определения опорных градиентов давления и ориентации участка.
