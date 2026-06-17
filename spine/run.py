"""Run the spine: pull -> features -> walk-forward backtest -> broad feed -> signal.json."""
import json, os, numpy as np, pandas as pd
from gridiron_spine import data, features, backtest, trade_solve

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
SEASONS = [2021, 2022, 2023, 2024, 2025]
FEATS = ["early_ppg", "z_opp"]

def main():
    print("pulling weekly opportunity data (QB/RB/WR/TE)…")
    df = data.pull_weekly(SEASONS)
    print(f"  {len(df):,} player-weeks, seasons {sorted(df.season.unique())}")

    d = features.build_player_season(df)
    print(f"  {len(d):,} player-seasons (backtest table)\n")

    print("=== walk-forward backtest: usage -> production (out-of-sample) ===")
    rep = {}
    for ts in [2024, 2025]:
        wf = backtest.walk_forward(d, FEATS, "late_ppg", train_max=ts - 1, test_season=ts)
        gap = backtest.evaluate_usage_gap(wf)
        rep[ts] = dict(n=wf["n"], r2_base=round(wf["r2_base"], 3), r2_full=round(wf["r2_full"], 3),
                       flag_improve_rate=round(gap["flag_improve_rate"], 3),
                       base_improve_rate=round(gap["base_improve_rate"], 3))
        lift = gap["flag_improve_rate"] - gap["base_improve_rate"]
        print(f"  test {ts} (n={wf['n']}): R2 {wf['r2_base']:.3f}->{wf['r2_full']:.3f} | "
              f"buy-flag improve {gap['flag_improve_rate']:.1%} vs base {gap['base_improve_rate']:.1%} ({lift:+.1%})")

    print("\n=== trade-solve self-test ===")
    sv = trade_solve.synthetic_validate()
    print(f"  Spearman {sv['spearman']:.3f} | median abs err {sv['median_abs_pct_err']:.1f}%")

    # ---- broad feed: most-recent qualifying season per player, all positions ----
    feed_df = features.build_feed(df)
    # buy flag = top-quartile gap within position cohort
    feed_df["q"] = feed_df.groupby("pos")["gap"].transform(lambda s: s.quantile(0.75))
    feed = {"meta": {"built_from": SEASONS, "backtest": rep, "trade_solve_selftest": sv,
                     "note": "join to Sleeper via players[].espn_id == key"},
            "players": {}}
    by_pos = {}
    for _, r in feed_df.iterrows():
        by_pos[r["pos"]] = by_pos.get(r["pos"], 0) + 1
        feed["players"][str(int(r.PlayerId))] = dict(
            name=r["name"], pos=r["pos"], team=r["team"], season=int(r.season),
            z_opp=round(float(r.z_opp), 2), gap=round(float(r.gap), 2),
            flag="buy" if r.gap >= r["q"] else None)
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "signal.json"), "w") as f:
        json.dump(feed, f, indent=2)
    print(f"\nwrote data/signal.json — {len(feed['players'])} players, by pos {by_pos}")

if __name__ == "__main__":
    main()
