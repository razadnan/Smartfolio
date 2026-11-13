import numpy as np
import pandas as pd
import pytest

from smartfolio.portfolio.hrp import hrp_portfolio


def test_hrp_basic_properties():
    symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ITC"]
    cov = pd.DataFrame(
        np.array([
            [0.0576, 0.0120, 0.0150, 0.0110, 0.0080],
            [0.0120, 0.0361, 0.0140, 0.0220, 0.0060],
            [0.0150, 0.0140, 0.0400, 0.0130, 0.0070],
            [0.0110, 0.0220, 0.0130, 0.0484, 0.0050],
            [0.0080, 0.0060, 0.0070, 0.0050, 0.0324]
        ]),
        index=symbols,
        columns=symbols
    )
    w = hrp_portfolio(cov)
    assert len(w) == 5
    assert np.isclose(w.sum(), 1.0)
    assert (w >= 0).all()
    assert (w <= 1.0).all()
    # Lowest volatility asset (ITC) should get higher weight than highest volatility (RELIANCE)
    assert w["ITC"] > w["RELIANCE"]


def test_hrp_edge_cases():
    # 2 assets
    cov_2 = pd.DataFrame([[0.04, 0.01], [0.01, 0.09]], index=["A", "B"], columns=["A", "B"])
    w_2 = hrp_portfolio(cov_2)
    assert np.isclose(w_2.sum(), 1.0)
    assert w_2["A"] > w_2["B"]

    # 1 asset
    cov_1 = pd.DataFrame([[0.04]], index=["A"], columns=["A"])
    w_1 = hrp_portfolio(cov_1)
    assert w_1["A"] == 1.0
