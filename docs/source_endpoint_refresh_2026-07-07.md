# Source endpoint refresh 2026-07-07

This refresh records a read-only recheck of official DOI, publisher,
repository and OpenAlex routes for the still-open source gates. It does not
release any `SOURCE_REQUIRED` or `source_candidate` gate: no new locally
auditable full text with SHA256 inventory, page/equation audit and reference
tests was obtained.

## Probe rules

- Publisher and repository landing pages are metadata unless they expose the
  article/report full text or an `ORIGINAL`/full-text bitstream.
- OpenAlex `oa_status=green` is not release evidence by itself; the actual
  landing page must expose a usable full-text file.
- HTTP 400/403 responses from official API/PDF endpoints without authorized
  context leave the gate at source acquisition.
- Any acquired PDF or scan must still be placed under `sources/primary` and
  recorded in `docs/primary_source_inventory.md` before formula audit.

## Endpoint and OA results

| Source gate | Official route checked | 2026-07-07 result | Gate decision |
| --- | --- | --- | --- |
| `TP-MULLER-STEINHAGEN-HECK-1986-SOURCE-GATE` | Elsevier TDM endpoint and publisher landing page for `10.1016/0255-2701(86)80008-3` | Elsevier API route returned HTTP 400 without an authorized API context; publisher route returned HTML landing metadata only. OpenAlex remained closed/no OA full-text route. | Keep `source_required`; obtain authorized article full text. |
| `TP-FRIEDEL-1979-SOURCE-GATE` | DOI/publisher route search from known citation variants | No DOI, publisher endpoint or archival scan was verified. The actionable route remains archival search for `3R International 18(7), 485, 1979` and/or the original Ispra paper E2. | Keep `source_required`; archival full text is missing. |
| `VOID-ZUBER-FINDLAY-1965-SOURCE-GATE` | ASME article/PDF endpoints for `10.1115/1.3689137` | ASME article and PDF endpoints returned HTTP 403 without authorized context. OpenAlex remained closed/no OA full-text route. | Keep `source_required`; local ASME full text is missing. |
| `REGIME-WOJTAN-URSENBACHER-THOME-2005-SOURCE-GATE` | Elsevier TDM endpoint, OpenAlex best OA landing, EPFL legacy/current repository records for `10.1016/j.ijheatmasstransfer.2004.12.012` | Elsevier API returned HTTP 400. OpenAlex marked a green EPFL landing but no `pdf_url`; the legacy EPFL URL redirected to the current repository landing. Exposed EPFL bitstreams were `license.txt` and a JPEG thumbnail only, with no `ORIGINAL`/full-text bitstream. | Keep `source_required`; repository landing is not release evidence. |
| `REGIME-TAITEL-BARNEA-DUKLER-1980-SOURCE-GATE` | Wiley article/PDF endpoints for `10.1002/aic.690260304` | Wiley endpoints returned HTTP 403 without authorized context. OpenAlex remained closed/no OA full-text route. | Keep `source_required`; local Wiley full text is missing. |
| `HTC-KANDLIKAR-1990-SOURCE-CANDIDATE` | ASME article/PDF endpoints for `10.1115/1.2910348` | ASME article and PDF endpoints returned HTTP 403 without authorized context. OpenAlex remained closed/no OA full-text route. | Keep `source_required`; local ASME full text is missing. |
| `HTC-GUNGOR-WINTERTON-1986-SOURCE-CANDIDATE` | Elsevier TDM endpoint and publisher landing page for `10.1016/0017-9310(86)90205-X` | Elsevier API route returned HTTP 400 without authorized API context; publisher route returned HTML landing metadata only. OpenAlex remained closed/no OA full-text route. | Keep `source_required`; local Elsevier full text is missing. |
| `HTC-WOJTAN-THOME-2005-PART-II-SOURCE-CANDIDATE` | Elsevier TDM endpoint, OpenAlex best OA landing, EPFL legacy/current repository records for `10.1016/j.ijheatmasstransfer.2004.12.013` | Elsevier API returned HTTP 400. OpenAlex marked a green EPFL landing but no `pdf_url`; the legacy EPFL URL redirected to the current repository landing. Exposed EPFL bitstreams were `license.txt` and a JPEG thumbnail only, with no `ORIGINAL`/full-text bitstream. | Keep `source_required`; repository landing is not release evidence. |
| `HTC-CHEN-1962-SOURCE-CANDIDATE` | OSTI PURL and record for `10.2172/4636495` | OSTI PURL still returned HTTP 200 `application/pdf` with `Content-Length 1533908`; the local source remains the only full-text intake ready candidate. | Keep `source_candidate`; rendered `F/S` graph review exists, but accepted interpolation/authoritative table, helper-to-runtime SI/axis mapping and source/reference HTC tests are still required before release. |

## Implementation effect

The manifest now records this endpoint/OA refresh in each affected
`access_evidence.endpoint_check` value. The release blockers did not change:
the only local full-text intake ready item remains Chen 1962, and its release
is still blocked by accepted `F/S` interpolation or authoritative table,
reviewed helper-to-runtime SI/axis mapping and source/reference HTC tests.
