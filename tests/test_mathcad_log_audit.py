from __future__ import annotations

import numpy as np
import pytest

from two_phase_closures import (
    darcy_friction_factor,
    rough_turbulent_friction_factor_ln,
    rough_turbulent_friction_factor_log10,
)


def test_rough_turbulent_term_documents_python_ln_vs_mathcad_log10_difference() -> None:
    relative_roughness = 1e-4 / (2.0 * 1.325e-2)

    python_current = rough_turbulent_friction_factor_ln(relative_roughness)
    mathcad_compatible = rough_turbulent_friction_factor_log10(relative_roughness)

    assert python_current > 0.0
    assert mathcad_compatible > 0.0
    assert python_current != pytest.approx(mathcad_compatible, rel=1e-12)


def test_darcy_friction_factor_keeps_current_default_and_allows_log10_audit() -> None:
    reynolds = np.asarray([1.0e5, 5.0e5, 1.0e6], dtype=float)
    relative_roughness = 1e-4 / (2.0 * 1.325e-2)

    current_default = darcy_friction_factor(reynolds, relative_roughness)
    explicit_natural = darcy_friction_factor(reynolds, relative_roughness, rough_log_base="natural")
    log10_variant = darcy_friction_factor(reynolds, relative_roughness, rough_log_base="log10")

    assert np.all(current_default > 0.0)
    assert np.all(log10_variant > 0.0)
    np.testing.assert_allclose(current_default, explicit_natural, rtol=0.0, atol=0.0)
    assert not np.allclose(current_default, log10_variant, rtol=1e-12, atol=0.0)


def test_darcy_friction_factor_rejects_unknown_rough_log_base() -> None:
    with pytest.raises(ValueError, match="Unsupported rough_log_base"):
        darcy_friction_factor(1.0e5, 1.0e-3, rough_log_base="ln10")

