from __future__ import annotations

from refrigerant_properties import (
    MathcadCO2SaturationProperties,
    SaturationState,
)


class CO2SaturationProperties(MathcadCO2SaturationProperties):
    """Compatibility name for the legacy Mathcad CO2 saturation tables."""


__all__ = ["CO2SaturationProperties", "SaturationState"]
