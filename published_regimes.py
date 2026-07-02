from __future__ import annotations

from experimental_regimes import FlowRegimeClassification, unknown_or_out_of_range_classification


def classify_horizontal_evaporator_regime_result(*args, **kwargs) -> FlowRegimeClassification:
    return unknown_or_out_of_range_classification(
        "Wojtan-Ursenbacher-Thome horizontal boiling map is not implemented."
    )


def classify_vertical_riser_regime_result(*args, **kwargs) -> FlowRegimeClassification:
    return unknown_or_out_of_range_classification(
        "Taitel-Barnea-Dukler vertical upflow map is not implemented."
    )
