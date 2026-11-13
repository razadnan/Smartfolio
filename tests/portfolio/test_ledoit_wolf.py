import numpy as np
import pandas as pd
import pytest
from smartfolio.portfolio.ledoit_wolf import ledoit_wolf_cov, sample_cov, validate_cov


def _rets(n=120, k=10):
    rng = np.random.default_rng(42)
    return pd.DataFrame(rng.normal(0, 0.01, (n, k)),
                        columns=[f"S{i}" for i in range(k)])


def test_shape_and_symmetry():
    cov, _ = ledoit_wolf_cov(_rets())
    assert cov.shape == (10, 10)
    assert np.allclose(cov.values, cov.values.T)


def test_shrinkage_in_range():
    _, s = ledoit_wolf_cov(_rets())
    assert 0.0 <= s <= 1.0


def test_psd():
    cov, _ = ledoit_wolf_cov(_rets())
    assert np.linalg.eigvalsh(cov.values).min() > 0


def test_lw_better_conditioned_than_sample():
    r = _rets(n=30, k=20)   # few observations, many assets
    lw, _ = ledoit_wolf_cov(r)
    assert np.linalg.cond(lw.values) < np.linalg.cond(sample_cov(r).values)


def test_nan_rejected():
    r = _rets()
    r.iloc[3, 2] = np.nan
    with pytest.raises(ValueError):
        ledoit_wolf_cov(r)