"""Data layer. Pulls weekly player opportunity data.

Two tiers:
  * pull_weekly() — committed CSVs on raw.githubusercontent (reachable everywhere,
    incl. sandboxed/CI). Targets, touches, red-zone targets, fantasy points.
  * NFLVERSE_RELEASES — richer features (snap share, routes, air yards) live on
    GitHub *release* assets. Those redirect to objects.githubusercontent, which some
    locked-down networks block. Enable when deployed where releases are reachable.
"""
import io, time, requests, pandas as pd, numpy as np
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "gridiron-spine/0.1"}
BASE = "https://raw.githubusercontent.com/hvpkod/NFL-Data/main/NFL-data-Players"

# Richer sources for deploy-time (snap share / air yards / routes). Blocked in some CI.
NFLVERSE_RELEASES = {
    "player_stats": "https://github.com/nflverse/nflverse-data/releases/download/player_stats/stats_player_week_{year}.parquet",
    "snap_counts":  "https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{year}.parquet",
}

def pull_weekly(seasons, positions=("WR", "RB", "TE"), max_week=18, workers=16):
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
            "Targets", "Touches", "RzTarget", "TotalPoints"]
    df = df[cols].copy()
    for c in ["Targets", "Touches", "RzTarget", "TotalPoints"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    # share of team skill-position targets that week
    team_tgt = df.groupby(["season", "week", "Team"])["Targets"].transform("sum")
    df["tgt_share"] = np.where(team_tgt > 0, df.Targets / team_tgt, 0.0)
    return df
