"""Run the spine end-to-end: pull -> features -> walk-forward backtest ->
trade-solve proof -> emit signal.json for the terminal frontend."""
import json, os, numpy as np, pandas as pd
from gridiron_spine import data, features, backtest, trade_solve

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repo root
DATA = os.path.join(ROOT, "data")

SEASONS = [2021, 2022, 2023, 2024, 2025]
FEATS = ["early_ppg", "z_opp"]

def main():
    print("pulling weekly opportunity data…")
    df = data.pull_weekly(SEASONS)
    print(f"  {len(df):,} player-weeks, seasons {sorted(df.season.unique())}")

    d = features.build_player_season(df)
    print(f"  {len(d):,} player-seasons after point-in-time split\n")

    print("=== walk-forward backtest: usage -> production (out-of-sample) ===")
    rep = {}
    for ts in [2024, 2025]:
        wf = backtest.walk_forward(d, FEATS, "late_ppg", train_max=ts - 1, test_season=ts)
        gap = backtest.evaluate_usage_gap(wf)
        cal = backtest.calibration(wf)
        rep[ts] = dict(
            n=wf["n"], r2_base=round(wf["r2_base"], 3), r2_full=round(wf["r2_full"], 3),
            gap_signal_spearman=round(gap["gap_resid_spearman"], 3),
            flag_improve_rate=round(gap["flag_improve_rate"], 3),
            base_improve_rate=round(gap["base_improve_rate"], 3),
        )
        lift = gap["flag_improve_rate"] - gap["base_improve_rate"]
        print(f"\n  test {ts}  (train <= {ts-1}, n={wf['n']})")
        print(f"    OOS R^2  early-ppg only : {wf['r2_base']:.3f}")
        print(f"    OOS R^2  + opportunity  : {wf['r2_full']:.3f}")
        print(f"    usage-gap 'buy' flag improve-rate: {gap['flag_improve_rate']:.1%} "
              f"vs base {gap['base_improve_rate']:.1%}  (lift {lift:+.1%})")
        print("    calibration (gap band -> mean production surprise):")
        for _, r in cal.iterrows():
            print(f"      gap {r['gap']:+.2f}  -> resid {r['mean_resid']:+.2f} ppg  (n={int(r['n'])})")

    print("\n=== trade-solve self-test (recover latent values from trades alone) ===")
    sv = trade_solve.synthetic_validate()
    print(f"  recovered {sv['n_solved']} players | Spearman {sv['spearman']:.3f} | "
          f"median abs err {sv['median_abs_pct_err']:.1f}%")

    # emit frontend feed for the most recent season, keyed by espn_id (= hvpkod PlayerId)
    latest = d[d.season == SEASONS[-1]].copy()
    q = latest.gap.quantile(0.75)
    feed = {"meta": {"season": SEASONS[-1], "backtest": rep,
                     "trade_solve_selftest": sv,
                     "note": "join to Sleeper via players[].espn_id == espn_id"},
            "players": {}}
    for _, r in latest.iterrows():
        feed["players"][str(int(r.PlayerId))] = dict(
            name=r["name"], pos=r["pos"], team=r["team"],
            z_opp=round(float(r.z_opp), 2), gap=round(float(r.gap), 2),
            early_ppg=round(float(r.early_ppg), 1),
            flag="buy" if r.gap >= q else None)
    os.makedirs(DATA, exist_ok=True)
    with open(os.path.join(DATA, "signal.json"), "w") as f:
        json.dump(feed, f, indent=2)
    print(f"\nwrote data/signal.json — {len(feed['players'])} players ({SEASONS[-1]})")

if __name__ == "__main__":
    main()
