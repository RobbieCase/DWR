"""Daily value-snapshot accumulator — the moat starter.

FantasyCalc exposes only *current* values. Value history and the panel you need for
the security-style charts and the mispricing backtest are NOT backfillable for free.
So this runs nightly in the Action and appends a dated snapshot to data/values/.
Every day it runs is a row of price history you can never recover otherwise.
"""
import json, os, datetime, requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "values")
COMBOS = [  # (label, isDynasty, numQbs, ppr, numTeams)
    ("dyn_1qb_ppr_12", "true", 1, 1, 12),
    ("dyn_sf_ppr_12",  "true", 2, 1, 12),
]

def snap():
    os.makedirs(OUT, exist_ok=True)
    today = datetime.date.today().isoformat()
    out = {"date": today, "source": "fantasycalc", "sets": {}}
    for label, dyn, qbs, ppr, tm in COMBOS:
        url = (f"https://api.fantasycalc.com/values/current?"
               f"isDynasty={dyn}&numQbs={qbs}&ppr={ppr}&numTeams={tm}")
        try:
            d = requests.get(url, timeout=30, headers={"User-Agent": "DWR/0.1"}).json()
            out["sets"][label] = {
                str(o["player"]["sleeperId"]): {
                    "v": o["value"], "t30": o.get("trend30Day", 0),
                    "or": o.get("overallRank")}
                for o in d if o.get("player", {}).get("sleeperId")}
            print(f"  {label}: {len(out['sets'][label])} players")
        except Exception as e:
            print(f"  {label}: FAILED {e}")
    path = os.path.join(OUT, f"{today}.json")
    with open(path, "w") as f:
        json.dump(out, f)
    print(f"wrote {path}")

if __name__ == "__main__":
    snap()
