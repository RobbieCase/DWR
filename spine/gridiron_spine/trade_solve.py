"""Revealed-preference value solver.

Every completed trade is an equation: value(side A) ~= value(side B). Stack all
observed trades into a sparse incidence system and solve for the implied value of
every asset at once (ridge least-squares, the same idea behind adjusted plus-minus
or Massey ratings). The output is a value scale derived from what managers ACTUALLY
did — not from a would-you-rather vote.

The scale is only identified up to an anchor, so we pin the overall scale to a prior
(market values, or all-equal) and let the trades shape the relatives.
"""
import numpy as np, scipy.sparse as sp
from scipy.stats import spearmanr

def solve_values(trades, asset_ids, prior=None, lam=1e-3, anchor=1.0):
    """trades: list of (sideA_ids, sideB_ids). asset_ids: ordered list of all assets."""
    idx = {a: i for i, a in enumerate(asset_ids)}
    N = len(asset_ids)
    data, ri, ci = [], [], []
    appear = np.zeros(N)
    for k, (A, B) in enumerate(trades):
        for p in A:
            if p in idx: data.append(1.0); ri.append(k); ci.append(idx[p]); appear[idx[p]] += 1
        for p in B:
            if p in idx: data.append(-1.0); ri.append(k); ci.append(idx[p]); appear[idx[p]] += 1
    Amat = sp.csr_matrix((data, (ri, ci)), shape=(len(trades), N))
    prior = np.full(N, 1.0) if prior is None else np.asarray(prior, float)
    M = (Amat.T @ Amat).toarray() + lam * np.eye(N) + anchor * np.ones((N, N)) / N
    b = lam * prior + anchor * prior.mean() * np.ones(N)
    x = np.linalg.solve(M, b)
    x *= prior.sum() / x.sum()            # rescale to prior's total (fixes the free scale)
    return {a: float(x[idx[a]]) for a in asset_ids}, appear

def synthetic_validate(N=120, M=900, seed=7):
    """Proof the math works: invent latent values, simulate rationally-accepted
    trades, recover values from the trades alone, compare to truth."""
    rng = np.random.default_rng(seed)
    true = np.exp(rng.normal(8.2, 0.7, N))
    ids = list(range(N))
    def near_trade():
        A = rng.choice(N, rng.integers(1, 3), replace=False)
        target, best = true[A].sum(), None
        for _ in range(40):
            B = rng.choice(N, rng.integers(1, 3), replace=False)
            if set(A) & set(B): continue
            d = abs(true[B].sum() - target)
            if best is None or d < best[0]: best = (d, B)
        return list(A), list(best[1])
    trades = [near_trade() for _ in range(M)]
    rec, appear = solve_values(trades, ids, prior=np.full(N, true.mean()))
    x = np.array([rec[i] for i in ids]); mask = appear >= 3
    return dict(spearman=float(spearmanr(x[mask], true[mask])[0]),
                median_abs_pct_err=float(np.median(np.abs(x[mask]-true[mask])/true[mask])*100),
                n_solved=int(mask.sum()))

# ---- real ingestion (runs where api.sleeper.app is reachable; not in locked CI) ----
def sleeper_ingest(league_ids, weeks=range(1, 19)):
    """Pull completed trades from public Sleeper leagues into (A, B) bundles.
    Walk previous_league_id on each league to get full multi-season history."""
    import requests
    trades = []
    for lid in league_ids:
        for w in weeks:
            try:
                txns = requests.get(
                    f"https://api.sleeper.app/v1/league/{lid}/transactions/{w}",
                    timeout=20).json()
            except Exception:
                continue
            for t in txns or []:
                if t.get("type") != "trade" or t.get("status") != "complete":
                    continue
                by_roster = {}
                for pid, rid in (t.get("adds") or {}).items():
                    by_roster.setdefault(rid, []).append(f"p:{pid}")
                for dp in (t.get("draft_picks") or []):
                    by_roster.setdefault(dp["owner_id"], []).append(
                        f"pick:{dp['season']}:{dp['round']}")
                sides = list(by_roster.values())
                if len(sides) == 2:           # 2-team trades feed the linear system cleanly
                    trades.append((sides[0], sides[1]))
    return trades
