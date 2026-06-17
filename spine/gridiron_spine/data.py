"""Data layer. Weekly player opportunity data for all four skill positions.

Committed CSVs on raw.githubusercontent (reachable everywhere incl. CI). Richer
features (snap share / routes / air yards) live on GitHub release assets and need
objects.githubusercontent reachable — wire those in on deploy (see NFLVERSE_RELEASES).
"""
import io, requests, pandas as pd, numpy as np
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "gridiron-spine/0.2"}
BASE = "https://raw.githubusercontent.com/hvpkod/NFL-Data/main/NFL-data-Players"
NFLVERSE_RELEASES = {
    "snap_counts": "https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{year}.parquet",
}

def pull_weekly(seasons, positions=("QB", "RB", "WR", "TE"), max_week=18, workers=16):
    sess = requests.Session(); sess.headers.update(UA)
    def grab(job):
        y, w, p = job
        try:
            r = sess.get(f"{BASE}/{y}/{w}/{p}.csv", timeout=25)
            if r.status_code != 200:
                return None
            d = pd.read_csv(io.StringIO(r.text))
            d["season"], d["week"], d["pos"] = y, w, p
            return d
        except Exception:
            return None
    jobs = [(y, w, p) for y in seasons for w in range(1, max_week + 1) for p in positions]
    with ThreadPoolExecutor(max_workers=workers) as ex:
        parts = [d for d in ex.map(grab, jobs) if d is not None]
    df = pd.concat(parts, ignore_index=True)
    cols = ["PlayerName", "PlayerId", "Team", "season", "week", "pos",
            "Targets", "Touches", "RzTarget", "TouchCarries", "RushingYDS",
            "PassingYDS", "TotalPoints"]
    df = df[cols].copy()
    num = ["Targets", "Touches", "RzTarget", "TouchCarries", "RushingYDS",
           "PassingYDS", "TotalPoints"]
    for c in num:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    team_tgt = df.groupby(["season", "week", "Team"])["Targets"].transform("sum")
    df["tgt_share"] = np.where(team_tgt > 0, df.Targets / team_tgt, 0.0)
    return df
