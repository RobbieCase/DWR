"""Feature construction with point-in-time discipline.

Each player-season is split at `early_cutoff`:
  * features come ONLY from weeks <= cutoff (what was knowable mid-season)
  * the outcome comes ONLY from weeks > cutoff
This separation is what makes the backtest honest — no feature can peek at its own
outcome window. Z-scores are computed within (season, position), using only that
season's early data, so they're available at decision time.
"""
import pandas as pd, numpy as np

OPP_COLS = ["tgt", "tch", "rz", "shr"]   # targets, touches, rz-targets, target-share (per game)

def _z(s):
    sd = s.std()
    return (s - s.mean()) / sd if sd and sd > 0 else s * 0.0

def build_player_season(df, early_cutoff=8, min_early=4, min_late=3, max_week=17):
    df = df[df.week <= max_week]
    rows = []
    for (pid, season, pos), g in df.groupby(["PlayerId", "season", "pos"]):
        e = g[g.week <= early_cutoff]
        l = g[g.week > early_cutoff]
        if len(e) < min_early or len(l) < min_late:
            continue
        rows.append(dict(
            PlayerId=pid, name=g.PlayerName.iloc[-1], team=g.Team.iloc[-1],
            season=season, pos=pos,
            tgt=e.Targets.mean(), tch=e.Touches.mean(), rz=e.RzTarget.mean(),
            shr=e.tgt_share.mean(), early_ppg=e.TotalPoints.mean(),
            late_ppg=l.TotalPoints.mean(),
        ))
    d = pd.DataFrame(rows)
    for c in OPP_COLS + ["early_ppg"]:
        d["z_" + c] = d.groupby(["season", "pos"])[c].transform(_z)
    d["z_opp"] = d[["z_" + c for c in OPP_COLS]].mean(axis=1)
    # usage gap: opportunity running ahead of scoring -> "underpriced by usage"
    d["gap"] = d["z_opp"] - d["z_early_ppg"]
    return d
