# Source endpoint refresh 2026-07-08

This refresh records a read-only recheck of official DOI, Crossref, OpenAlex,
publisher, repository and OSTI routes for the still-open source gates. A
follow-up Python `urllib` HEAD/Crossref probe on 2026-07-08 refined the
publisher endpoint evidence without obtaining any new full-text payload. It
does not release any `SOURCE_REQUIRED` or `source_candidate` gate: no new
locally auditable full text with SHA256 inventory, page/equation audit and
reference tests was obtained.

## Probe rules

- DOI, Crossref and publisher landing metadata are bibliographic evidence, not
  formula-release evidence.
- OpenAlex `oa_status=green` is not release evidence by itself; the landing
  route must expose a usable full-text PDF or bitstream.
- HTTP 400/403/429 responses from official API/PDF endpoints without an
  authorized full-text payload leave the gate at source acquisition.
- Any acquired PDF, scan or authorized full-text export must still be placed
  under `sources/primary` and recorded in `docs/primary_source_inventory.md`
  before formula audit.

## DOI and metadata results

| Source gate | DOI/Crossref/OpenAlex result on 2026-07-08 | Gate decision |
| --- | --- | --- |
| `TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE` | DOI redirected to Elsevier landing HTTP 200 for `10.1016/0255-2701(86)80008-3`; Crossref confirmed the journal article metadata, 22 references and two Elsevier TDM links; OpenAlex remained `is_oa=false`, `oa_status=closed`, no `oa_url`. | Keep `source_required`; obtain authorized article full text. |
| `TP-FRIEDEL-1979-SOURCE-GATE` | Crossref bibliographic searches for Friedel 1979/Ispra/3R International variants returned unrelated pressure-drop records and did not verify a primary DOI, publisher endpoint or archival scan. The MSH Crossref reference list does identify Friedel, `3R Int.` 18(7), page 485, 1979, article title `Improved friction pressure drop correlations for horizontal and vertical two-phase flow`. | Keep `source_required`; archival full text is missing. |
| `VOID-ZUBER-FINDLAY-1965-SOURCE-GATE` | DOI route for `10.1115/1.3689137` reached the ASME landing with HTTP 403; Crossref confirmed journal article metadata and two links; OpenAlex work `W2019758240` remained closed with no OA URL or PDF URL. | Keep `source_required`; local ASME full text is missing. |
| `REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE` | Crossref confirmed Part I metadata for `10.1016/j.ijheatmasstransfer.2004.12.012`; OpenAlex remained green only to EPFL landing `http://infoscience.epfl.ch/record/52074`, not a PDF URL. | Keep `source_required`; repository landing is not release evidence. |
| `REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE` | DOI route for `10.1002/aic.690260304` reached Wiley with HTTP 403; Crossref confirmed the exact title `Modelling flow pattern transitions for steady upward gas-liquid flow in vertical tubes`, AIChE Journal 26(3), 345-354, 41 references and three Wiley PDF/TDM links; OpenAlex work `W2100537585` remained closed with no OA URL or PDF URL. | Keep `source_required`; local Wiley full text is missing. |
| `HTC-KANDLIKAR-1990-SOURCE-CANDIDATE` | DOI route for `10.1115/1.2910348` reached ASME with HTTP 403; Crossref confirmed journal article metadata and two links; OpenAlex work `W2120660956` remained closed with no OA URL or PDF URL. | Keep `source_required`; local ASME full text is missing. |
| `HTC-GUNGOR-WINTERTON-1986-SOURCE-CANDIDATE` | DOI redirected to Elsevier landing HTTP 200 for `10.1016/0017-9310(86)90205-X`; Crossref confirmed journal article metadata and two links; OpenAlex remained `is_oa=false`, `oa_status=closed`, no `oa_url`. | Keep `source_required`; local Elsevier full text is missing. |
| `HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE` | Crossref confirmed Part II metadata for `10.1016/j.ijheatmasstransfer.2004.12.013`; OpenAlex remained green only to EPFL landing `http://infoscience.epfl.ch/record/52064`, not a PDF URL. | Keep `source_required`; repository landing is not release evidence. |
| `HTC-CHEN-1962-SOURCE-CANDIDATE` | OSTI record `https://www.osti.gov/biblio/4636495` returned HTTP 200 HTML and OSTI PURL `https://www.osti.gov/servlets/purl/4636495` returned HTTP 200 `application/pdf`. | Keep `source_candidate`; local intake exists, but release-grade formula/runtime proof is still missing. |

## Publisher endpoint results

| Route | 2026-07-08 endpoint result | Interpretation |
| --- | --- | --- |
| ASME Zuber-Findlay PDF `http://asmedigitalcollection.asme.org/heattransfer/article-pdf/87/4/453/5908192/453_1.pdf` | HTTP 403 `text/html` after HTTPS redirect. | No unauthenticated full-text payload. |
| ASME Kandlikar PDF `http://asmedigitalcollection.asme.org/heattransfer/article-pdf/112/1/219/5644274/219_1.pdf` | HTTP 403 `text/html` after HTTPS redirect. | No unauthenticated full-text payload. |
| Wiley Taitel-Barnea-Dukler TDM API `https://api.wiley.com/onlinelibrary/tdm/v1/articles/10.1002%2Faic.690260304` | HTTP 400 with message `No TDM Client Token was found in the request`. | TDM route exists but needs authorized token; no unauthenticated full-text payload. |
| Wiley Taitel-Barnea-Dukler PDF `https://aiche.onlinelibrary.wiley.com/doi/pdf/10.1002/aic.690260304` and `https://onlinelibrary.wiley.com/doi/pdf/10.1002/aic.690260304` | HTTP 403 `text/html`. | No unauthenticated full-text payload. |
| Elsevier MSH TDM endpoint `https://api.elsevier.com/content/article/PII:0255270186800083?httpAccept=text/plain` | HTTP 400 `text/xml`. | No authorized API full-text response. |
| Elsevier Gungor-Winterton TDM endpoint `https://api.elsevier.com/content/article/PII:001793108690205X?httpAccept=text/plain` | One unauthenticated probe returned HTTP 429 `application/json`; follow-up Python HEAD returned HTTP 400 `text/xml` without authorized API context. | No authorized full-text payload; not release evidence. |
| Elsevier WUT Part I TDM endpoint `https://api.elsevier.com/content/article/PII:S0017931005000268?httpAccept=text/plain` | HTTP 400 `text/xml`. | No authorized API full-text response. |
| Elsevier WUT Part II TDM endpoint `https://api.elsevier.com/content/article/PII:S001793100500027X?httpAccept=text/plain` | HTTP 400 `text/xml`. | No authorized API full-text response. |
| EPFL legacy WUT Part I/II landing pages `http://infoscience.epfl.ch/record/52074` and `http://infoscience.epfl.ch/record/52064` | HTTP 429 `text/html` during direct landing-page probe. | Rate-limited landing probe; no new full-text bitstream evidence. |
| OSTI Chen PURL `https://www.osti.gov/servlets/purl/4636495` | HTTP 200 `application/pdf`. | Confirms the existing local `source_candidate` full-text route only. |

## Implementation effect

The manifest records this refresh in `access_evidence` for the affected gates,
and policy docs include this file as a previous audit document. The release
blockers did not change:

- MSH, Zuber-Findlay, Taitel-Barnea-Dukler, Kandlikar and Gungor-Winterton have
  official bibliographic records but still no locally inventoried full text.
- Friedel remains an archival-source acquisition problem with no reliable
  primary DOI/publisher endpoint found by the refreshed Crossref search.
- WUT Part I/II still have green EPFL landing metadata but no release-grade
  journal full text; local TH2978 remains only dissertation guidance.
- Chen 1962 remains the only local full-text intake-ready heat-transfer
  candidate; rendered `F/S` graph review exists, but accepted interpolation or
  an authoritative table, helper-to-runtime SI/axis mapping and source/reference
  HTC tests are still required.
