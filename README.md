# DWR — Dynasty War Room

A browser dynasty terminal: live league sync, player intelligence, and a backtested
usage signal. "Bloomberg terminal" in spirit — pulls live data, models it, surfaces
mispricings — but football-statistics-forward, not finance-skinned.

## Layout
    index.html              terminal frontend (served by GitHub Pages)
    data/signal.json        backtested usage signal feed (rebuilt nightly)
    data/values/            dated FantasyCalc value snapshots (the price panel, accumulating)
    spine/                  python data + modeling spine
      gridiron_spine/       data, features, backtest, trade_solve
      run.py                pull -> features -> walk-forward backtest -> signal.json
      snapshot.py           nightly value-snapshot accumulator
      requirements.txt
    .github/workflows/spine.yml   nightly Action (runs spine + snapshot, commits data/)

## How it runs
- The Action runs nightly (and on demand). A GitHub-hosted runner has open internet,
  so it reaches data and APIs a sandbox blocks. It commits refreshed `data/` back to
  the repo using the built-in `GITHUB_TOKEN` — no personal token needed.
- The frontend fetches `./data/signal.json` and joins to the Sleeper players map via
  `espn_id`, lighting up the live usage signal + out-of-sample backtest context.

## Signal — honest state
Out-of-sample, top-quartile **usage-gap** players (opportunity ahead of scoring)
improved their later scoring at +5 to +10pp over base rate (38.7% vs 28.5%, 2025).
The trade-solve recovers latent values from trades at Spearman ~0.998 in self-test.
Single-source for now; the lift grows with snap/route/air-yards features and the live
trade feed (next iteration — they need the deploy environment to pull).

## Deploy
1. Push to `robbiecase/DWR`.
2. Settings -> Pages -> deploy from `main`, root. (`.nojekyll` is included.)
3. Actions tab -> run `spine` once (or wait for the nightly cron) to refresh `data/`.
4. Terminal lives at the Pages URL; sync your Sleeper username and go.

## Run the spine locally
    pip install -r spine/requirements.txt
    python spine/run.py          # rebuilds data/signal.json
    python spine/snapshot.py     # appends today's value snapshot
