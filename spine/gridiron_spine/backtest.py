"""Point-in-time, walk-forward backtest harness.

Discipline enforced here:
  * train seasons are strictly EARLIER than the test season (no future leakage)
  * features are early-window only; the target is late-window only (set in features.py)
  * survivorship: build_player_season includes everyone who met the games threshold
    that season, not just players still relevant today
  * calibration is reported, not just accuracy — a signal that's right 60% of the
    time is only useful if its confidence is honest.
"""
import numpy as np, pandas as pd
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score
from scipy.stats import spearmanr

def walk_forward(d, feats, target, train_max, test_season, model=None):
    tr = d[d.season <= train_max]
    te = d[d.season == test_season]
    if len(te) == 0:
        return None
    model = model or Ridge(alpha=1.0)
    base = Ridge(alpha=1.0).fit(tr[["early_ppg"]], tr[target])
    full = model.fit(tr[feats], tr[target])
    pb = base.predict(te[["early_ppg"]])
    pf = full.predict(te[feats])
    return dict(
        test_season=test_season, n=len(te),
        r2_base=r2_score(te[target], pb),
        r2_full=r2_score(te[target], pf),
        spearman_full=spearmanr(te[target], pf)[0],
        residual=te[target].values - pb,   # production beyond what early scoring predicts
        frame=te,
    )

def evaluate_usage_gap(wf):
    """Decision-level test: do top-quartile usage-gap players (opportunity ahead of
    scoring) improve their scoring in the late window more often than the field?"""
    te = wf["frame"].copy()
    te["resid"] = wf["residual"]
    q = te.gap.quantile(0.75)
    flagged = te[te.gap >= q]
    return dict(
        test_season=wf["test_season"],
        gap_resid_spearman=spearmanr(te.gap, te.resid)[0],
        flag_improve_rate=float((flagged.late_ppg > flagged.early_ppg).mean()),
        base_improve_rate=float((te.late_ppg > te.early_ppg).mean()),
        n_flagged=int(len(flagged)),
    )

def calibration(wf, bins=5):
    te = wf["frame"].copy(); te["resid"] = wf["residual"]
    te["band"] = pd.qcut(te.gap, bins, labels=False, duplicates="drop")
    g = te.groupby("band").agg(gap=("gap", "mean"),
                               mean_resid=("resid", "mean"),
                               n=("resid", "size")).reset_index()
    return g
