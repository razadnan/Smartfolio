"""
hrp.py — Hierarchical Risk Parity (HRP) Portfolio Optimization.
Invented by Marcos López de Prado (2016).
Replaces quadratic programming with tree clustering and recursive bisection,
completely avoiding matrix inversion and singularity instabilities.
"""
import numpy as np
import pandas as pd
import scipy.cluster.hierarchy as sch
from scipy.spatial.distance import squareform


def get_quasi_diag(link: np.ndarray) -> list[int]:
    """Sort clustered items by hierarchical tree order."""
    link = link.astype(int)
    sort_ix = pd.Series([link[-1, 0], link[-1, 1]])
    num_items = link[-1, 3]
    while sort_ix.max() >= num_items:
        sort_ix.index = range(0, sort_ix.shape[0] * 2, 2)
        df0 = sort_ix[sort_ix >= num_items]
        i = df0.index
        j = df0.values - num_items
        sort_ix[i] = link[j, 0]
        df0 = pd.Series(link[j, 1], index=i + 1)
        sort_ix = pd.concat([sort_ix, df0]).sort_index()
        sort_ix.index = range(sort_ix.shape[0])
    return sort_ix.tolist()


def get_cluster_var(cov: pd.DataFrame, cluster_items: list[str]) -> float:
    """Calculate cluster variance using inverse-variance weights."""
    cov_slice = cov.loc[cluster_items, cluster_items].values
    diag = np.diag(cov_slice)
    inv_var = 1.0 / np.maximum(diag, 1e-8)
    w = inv_var / inv_var.sum()
    c_var = float(w @ cov_slice @ w)
    return max(c_var, 1e-8)


def get_rec_bisection(cov: pd.DataFrame, sort_ix: list[str]) -> pd.Series:
    """Recursively bisect the tree and allocate risk inversely proportional to variance."""
    weights = pd.Series(1.0, index=sort_ix)
    clusters = [sort_ix]
    while len(clusters) > 0:
        clusters = [c[start:end] for c in clusters
                    for start, end in ((0, len(c) // 2), (len(c) // 2, len(c)))
                    if len(c) > 1]
        for i in range(0, len(clusters), 2):
            c1 = clusters[i]
            c2 = clusters[i + 1]
            var1 = get_cluster_var(cov, c1)
            var2 = get_cluster_var(cov, c2)
            alpha = 1.0 - var1 / (var1 + var2)
            weights[c1] *= alpha
            weights[c2] *= (1.0 - alpha)
    return weights


def hrp_portfolio(cov: pd.DataFrame) -> pd.Series:
    """
    Compute Hierarchical Risk Parity weights from a covariance matrix.
    
    Parameters:
        cov : pd.DataFrame (N x N covariance matrix with index & columns = symbols)
    
    Returns:
        pd.Series of portfolio weights summing to 1.0
    """
    if cov.empty or len(cov) < 2:
        return pd.Series([1.0], index=cov.index if not cov.empty else ["ASSET"])

    # 1. Compute correlation matrix
    diag = np.sqrt(np.diag(cov.values))
    denom = np.outer(diag, diag)
    corr = cov.values / np.maximum(denom, 1e-8)
    corr = np.clip(corr, -1.0, 1.0)
    np.fill_diagonal(corr, 1.0)

    # 2. Distance matrix: d_{i,j} = sqrt(0.5 * (1 - rho_{i,j}))
    dist = np.sqrt(np.maximum(0.0, 0.5 * (1.0 - corr)))
    np.fill_diagonal(dist, 0.0)

    # 3. Hierarchical clustering (single linkage)
    condensed_dist = squareform(dist, checks=False)
    link = sch.linkage(condensed_dist, method="single")

    # 4. Quasi-diagonalization
    sort_ix_num = get_quasi_diag(link)
    sorted_symbols = [cov.index[i] for i in sort_ix_num]

    # 5. Recursive bisection
    w = get_rec_bisection(cov, sorted_symbols)
    w = w.loc[cov.index]  # restore original symbol ordering
    w = w / w.sum()
    return w
