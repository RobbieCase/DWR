# DWR / Dynasty Terminal — Roadmap

Living backlog. Open items at top; shipped log at the bottom.

---

## Open / next

### A. Trade — browse other teams' rosters
Current trade terminal has target suggestions and a synced league pool, but not a clean way to click into another dynasty team and inspect that roster.

Want:
- In the trade feature, show the synced league's other teams as clickable roster views.
- Clicking a team opens that roster inside the trade surface: player, position, value, buy flag / gap context, owner.
- From that roster view, one click adds a player to **I get**.
- This should connect naturally to the buy-low target suggestions, not replace them.

### B. League tab — loaded league should stay useful
After a league is loaded, clicking the `lg` tab should show the loaded league state, not feel like a reset/search screen.

Want:
- If `dwr_myleague` exists, the League tab should open directly to the saved league/teams view.
- From the league view, users should be able to click into other managers' teams/rosters.
- Add a clear "change league" / "sync another league" path without losing the loaded-league workflow.

### C. League season selector
Current league sync uses a typed season field and has recently defaulted to 2025. This should become a deliberate selector.

Want:
- Default to the current/upcoming fantasy season: **2026**.
- Replace free-text season entry with a selection list going back to **2020**.
- Keep this driven by current date / Sleeper season state when possible, but avoid users having to type a year.

### D. News — bug fix + source expansion
Bug: when a player has no matched news, the player news panel currently populates around-the-league / random articles. That is misleading.

Fix:
- If a player has no matched news, show a clean empty state: "no recent matched headlines."
- Do **not** show unrelated articles inside a player-specific news panel.
- If we want general headlines, put them in a separately labeled global news wire.

Expansion:
- Pull in news from other prominent sports news websites beyond ESPN where feasible.
- Likely sources to investigate: NFL.com, CBS Sports, Yahoo, Rotoworld/NBC, The Athletic headlines if legally/reachably available, team sites.
- Many sources will block browser CORS; if so, build an Action-side `data/news.json` aggregator.
- Eventually: identify reliable beat reporters and pull from their accounts/feed endpoints, then keyword/entity-match to players and teams.

### E. Stats placement
Current year-by-year stat history ships as its own `stat` tab. That is too separate from the main player context.

Want:
- Remove the standalone `stat` tab.
- Move compact stat-history access next to **yoe** in the player header, or embed it naturally in existing tabs.
- The goal: stats feel like context on the player, not another top-level surface.
- Preserve the existing ESPN year-by-year data and position-appropriate categories.

### F. Value-history backfill — decision pending
History **is** recoverable from DynastyProcess git history (~349 dated commits), but those are **FantasyPros-ECR-derived**, not FantasyCalc — a *parallel* series, not a clean backfill of our moat. Decide:
1. Build a separate DynastyProcess-derived historical series (instant multi-year trends for charts/watchlists, labeled as a different source), or
2. Keep FantasyCalc forward-only (one clean source, slow to deepen).
Recommendation: option 1 if we want multi-year visuals before the FantasyCalc series matures.

### G. Full mode-aware surfaces (in-season vs offseason)
The header **mode badge** ships (offseason / in-season · wk N, from Sleeper `/state/nfl`). Still to do: actually *switch* default surfaces and emphasis by phase —
- Offseason: trade market, rookie/pick analysis, historical trends, portfolio.
- In-season: lead with live game-to-game data, weekly usage, matchup context.
- Add the ESPN **gamelog** (game-by-game) to the stat tab for the in-season current row.
Can't be validated until the season; build the scaffolding, prove it in the fall.

### H. Trade verdict — deeper
Revealed-values basis + contention-window tilt ship. Next: scale the consolidation tax by the league's actual roster/bench/taxi settings (vs the current flat 4%/body), and ultimately let the revealed-preference solver *learn* the discount.

---

## In flight / blocked
- **Live-verify the revealed-preference solve** on a real league (needs a Sleeper username; client-side, no hardcoding).
- **Spine-side name-keying** for `signal.json` (deterministic join; spawned task).
- **Survival → value multiplier**: aging survival ships as context; a usable price multiplier needs a proper model (Cox w/ covariates), not just more years.
- **Vegas prop-implied points** — deferred to the season.
- **In-season lead-lag validation** — only provable once games are played.

---

## Shipped
- **Moat-clock fix** — value snapshots on the orphan `data` branch (local pushes can't clobber).
- **Screener** — sortable mispricing board over the universe.
- **Pick auto-derivation** — owned picks from Sleeper's traded-pick ledger, format-scaled.
- **signal.json name-join fix** — repaired buy flags app-wide (was espn_id-keyed, ~0 hits).
- **nflverse snap + air-yards** (display) — incl. the stats_player air-yards source fix.
- **Gap-aware intrinsic/edge** — edge reflects the backtested usage gap, not just the age tier.
- **Value-history sparkline** — player market tab, from the `data` branch snapshots.
- **Client-side revealed-preference trade-solve** — solves your synced league's real trades (no league id hardcoded).
- **KM survival aging** (context) — fit on deep 2010–25 nflverse history; "aging outlook" panel.
- **Trade 1a/1b** — buy-low fill-needs (gap + flag + snap + youth − price), ALL/QB/RB/WR/TE tabs, top 8, with "why".
- **Trade 1c** — verdict value-basis (market | revealed) + contention-window tilt; **fixed an inverted verdict** (give vs get).
- **Consolidation tax fix** — counts real roster bodies only (picks & throw-ins excluded), capped.
- **Watchlists / portfolio tracking** — ☆ any player; board of edge/gap/value + "since tracked" deltas. The moat clock, personal.
- **News** — ESPN feed, entity/name-matched to the player, with an around-the-league fallback.
- **Year-by-year stat history** — ESPN athlete stats by season (`stat` tab), position-appropriate.
- **Mode badge** — offseason/in-season indicator from Sleeper state.
