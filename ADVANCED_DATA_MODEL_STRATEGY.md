# DWR Advanced Data + Model Strategy

This document is the answer to a product risk: DWR cannot win by being a polished frontend over Sleeper, ESPN, and FantasyCalc. The durable edge has to come from a data spine that reconciles sources, measures uncertainty, learns league behavior, and turns noisy football signals into decisions.

The goal is not "more data" by itself. The goal is source-aware synthesis: same player, same league, same decision, with multiple independent views of truth and a model that can explain when those views disagree.

---

## Product Thesis

DWR should become a dynasty decision engine with four defensible moats:

1. **Identity graph**: a reliable cross-provider player/team/league map that makes joins auditable instead of magical.
2. **Source comparison layer**: every number knows where it came from, how stale it is, and whether other sources agree.
3. **Predictive model layer**: usage, age, depth, news, value history, and league behavior are modeled together, not shown as isolated API fields.
4. **Action layer**: outputs are trade targets, roster risks, watchlist alerts, rookie/pick moves, and "why changed" explanations.

If a feature only mirrors an API response, it is a source panel. It becomes a DWR feature only when it is joined, compared, validated, and used in a decision.

---

## Data Overhaul

### 1. Build A Canonical Entity Graph

Current joins are still too brittle. Before adding more sources, DWR needs a first-class identity artifact:

- `data/identity/players.json`: canonical player id, Sleeper id, ESPN id, nflverse id, gsis id, PFR id, Sportradar/PFF ids if available, normalized names, aliases, birth date, position history, team history.
- `data/identity/teams.json`: canonical team id, Sleeper abbreviation, ESPN team id, nflverse abbreviation, historical aliases.
- `data/identity/join_report.json`: coverage by source, season, position, join method, stale/collision flags.
- `data/identity/exceptions.json`: hand-audited collisions like duplicate names, renamed players, rookies sharing old-player names, and team/position conflicts.

Rules:
- Prefer true ids over names.
- If using names, require position plus a temporal guard.
- If two candidates share name/position, require birth date, team, draft year, or explicit exception.
- Store join confidence, not only the selected join.
- Treat "unmatched" as a valid state, not a UI failure.

### 2. Split Raw, Normalized, And Feature Artifacts

The spine should stop emitting only final features. It should emit layers:

- `raw/`: source-shaped pulls, minimally transformed.
- `normalized/`: canonical schemas keyed by DWR ids.
- `features/`: model-ready player-season/player-week/player-day tables.
- `reports/`: coverage, freshness, conflicts, validation, backtest outputs.
- `app/`: compact JSON files designed for the browser.

This makes the system debuggable. When DWR says "player has no usage signal," we should know whether that means no raw data, failed identity join, stale season, insufficient games, or filtered by model rules.

### 3. Add Source Scorecards

Every data source should have a source contract:

- Coverage: players/teams/seasons/positions covered.
- Freshness: last successful pull and source timestamp.
- Join confidence: id join, name+position, manual override, unresolved.
- Failure mode: network blocked, CORS, schema drift, stale endpoint, missing current season.
- Legal/reachability status: browser-safe, Action-only, paid/manual, not allowed.

This becomes a visible "source health" layer and a development guardrail.

---

## Source Expansion

### Core Open/Reachable Sources

These should become the default backbone:

- **Sleeper**: live player universe, leagues, rosters, transactions, traded picks, schedules.
- **FantasyCalc**: current dynasty market anchor and daily market snapshots.
- **ESPN**: stats, gamelogs, news, depth charts, injuries where reachable.
- **nflverse / nflfastR / player_stats / snap_counts / rosters**: weekly production, advanced passing/rushing/receiving, snaps, air yards, ids, ages.
- **Pro Football Reference ids via nflverse**: useful as an identity bridge and historical cross-check.
- **DynastyProcess / FantasyPros-derived historical values**: parallel historical context, clearly labeled as a different market source.

### High-Value Next Sources To Investigate

Add only if legally and technically reachable:

- **Official NFL injury reports**: practice participation, game status, injury type.
- **Depth/news from team sites**: especially beat-reporter-like local context when structured feeds exist.
- **CBS / Yahoo / NBC Rotoworld / NFL.com headlines**: Action-side aggregation if browser CORS blocks.
- **Vegas lines and player props**: implied team totals, game environment, prop-implied opportunity once season is live.
- **Rookie/draft data**: draft capital, age, production profile, combine/pro day, college dominator, early declare, team landing spot.
- **Contract/cap data**: role security, dead money, team incentive to keep/cut/extend.

### Paid Or Restricted Sources

These could materially improve the model, but should not be assumed:

- PFF routes, grades, receiving alignment, pass-block usage.
- SIS charting.
- FTN/DVOA/advanced usage products.
- Sharp sportsbook props.

If used, they should be optional private inputs or manually imported artifacts. Do not build a core dependency on restricted scraping.

---

## Compare And Concatenate Strategy

More sources create contradictions. DWR should not blindly concatenate.

### Source Agreement Tables

For each key concept, create a comparison artifact:

- Depth role: ESPN depth, Sleeper depth order, team site chart, snap share, routes.
- Injury status: Sleeper injury, ESPN injury, official report, news entity match.
- Usage: nflverse stats, snap counts, ESPN gamelogs, FantasyCalc movement.
- Value: FantasyCalc current, DWR revealed, DWR intrinsic, DynastyProcess historical, pick model.

Each comparison row should include:

- `source_value`
- `source_timestamp`
- `confidence`
- `staleness`
- `agreement_group`
- `conflict_reason`

### Consensus Rules

Use a conservative source hierarchy:

- If sources agree, raise confidence.
- If sources conflict, show the conflict and avoid overconfident model movement.
- If a source is stale, downweight it.
- If a player has thin identity confidence, block derived signals until resolved.

### Feature Store Shape

Create player-week and player-day feature tables:

- `player_week_features`: usage, snaps, routes/proxy, air yards, team environment, depth status, injuries, fantasy points.
- `player_day_features`: market value, news flags, injury changes, depth changes, roster transaction changes.
- `league_player_features`: roster ownership, revealed value, manager/team context, contention window.

This lets the model ask: "Did usage change before market changed?" and "Did depth/news explain value movement?"

---

## Model Overhaul

### 1. Replace Intrinsic v0 With A Real Player Value Model

Current intrinsic is useful scaffolding, but it is still a heuristic:

`market * age curve * momentum * usage-gap tilt`

A stronger model should estimate expected future dynasty value directly:

- Target: future FantasyCalc value change, future production, or a blended utility target.
- Horizon: 4 weeks, rest of season, 1 year, 2 years.
- Position-specific models.
- Inputs: age, draft capital, experience, prior production, current usage, usage trend, team environment, injuries, depth, market liquidity, value momentum.
- Output: expected value, uncertainty, and reason codes.

Recommended first pass:

- Gradient boosted trees or regularized linear models by position.
- Walk-forward validation by season.
- Compare against simple baselines: current market, age-only, usage-only, momentum-only.
- Ship only if it beats baseline out of sample.

### 2. Role And Opportunity Model

Instead of a single usage gap, build a role state model:

- QB: pass volume, designed rush, scramble tendency, team pass rate, pressure environment.
- RB: carry share, target share, goal-line role, two-minute role, snap share.
- WR: route participation proxy, target share, air-yards share, first-read proxy if available, slot/wide role if available.
- TE: route participation proxy, target share, inline/slot role if available, red-zone role.

Output should be:

- Current role tier.
- Role trend.
- Role fragility.
- Opportunity vs production gap.
- Confidence based on games and source coverage.

### 3. Survival And Aging Model

The current Kaplan-Meier survival context is useful, but not enough for pricing.

Next step:

- Fit position-specific survival or hazard models with covariates.
- Covariates: age, experience, production tier, draft capital, recent role, injury history, position, size where useful.
- Output: probability of remaining fantasy-relevant over 1/2/3/5 years.
- Convert survival into a value multiplier only after validation.

This becomes a real dynasty horizon model instead of a hand-coded age curve.

### 4. Revealed Preference Model

The revealed solver is the most differentiated piece, but needs hardening:

- Persist solved values by league/season.
- Track trades, solved players, market-anchored players, and solve confidence.
- Separate player values from pick discounts.
- Learn manager-specific preferences if enough trades exist.
- Learn league-wide pick/player/liquidity discounts.
- Use robust regression or Bayesian priors to reduce weird small-sample solves.
- Compare solved values against later trades to validate.

Eventually, revealed values should answer:

- Does this league pay up for QBs?
- Does this league discount injured players?
- Are picks overpriced or underpriced?
- Which managers overpay for contenders/youth/rookies?

### 5. Pick And Rookie Model

Pick values are too flat.

Build:

- Pick provenance and confidence.
- Projected finish distribution from season sim.
- Rookie class strength and tier cliffs.
- Format-sensitive QB premium.
- Historical pick outcome curves by round, slot, position, draft capital.
- Revealed pick discounts from actual league trades.

Output:

- Pick value range, not a point estimate.
- Confidence and provenance.
- "Why this pick moved" explanations.

### 6. News And Injury Model

News should not be a feed. It should be a signal classifier.

Pipeline:

- Aggregate legally reachable headlines/articles.
- Entity-match to player/team.
- Classify: injury, return, role, transaction, coach quote, contract, off-field, noise.
- Attach severity and confidence.
- Compare with value movement and depth movement.

Output:

- Player-specific matched headlines only.
- Watchlist alerts.
- "Why changed" explanations.
- Seasonal validation: which news classes predict value movement?

---

## Backtesting And Validation

Every model upgrade needs a validation report.

### Required Reports

- `reports/model_backtest.json`: by season, position, horizon, metric.
- `reports/source_coverage.json`: source freshness and coverage.
- `reports/join_conflicts.json`: unresolved identity collisions.
- `reports/lead_lag.json`: usage/news/depth changes vs later market movement.
- `reports/revealed_validation.json`: solved values vs later accepted trades.

### Baselines

Never ship a model without comparing to:

- Current market value.
- Current value momentum.
- Age-only heuristic.
- Usage-only heuristic.
- Position average.

If a new model does not beat these out of sample, it can remain context, not decision logic.

### Metrics

Use several metrics because no single one captures dynasty utility:

- Directional accuracy: did value go up/down?
- Calibration: did predicted probability match observed frequency?
- Rank correlation: did top opportunities outperform?
- Lift by decile/quartile.
- Error by position, age bucket, and value tier.
- Coverage-adjusted performance.

---

## Action Surfaces That Prove It Is Not An API Wrapper

### Player Page

Should answer:

- What changed?
- Which sources agree?
- Is the market ahead of or behind the model?
- Is the player liquid or thinly traded?
- Is the role stable, rising, or fragile?

### Screener

Should rank:

- Market vs intrinsic gap.
- Market vs revealed gap.
- Usage lead-lag candidates.
- Depth/news/injury role movers.
- Confidence-adjusted opportunities.

### Watchlist

Should show event cards:

- Value moved.
- Role changed.
- Depth changed.
- News matched.
- Injury status changed.
- Model confidence changed.

### Trade Market

Should convert edges into targets:

- Which manager rosters the target?
- Why they might sell.
- Why they fit my roster.
- Which asset type this league discounts.
- What offer structure is likely fair.

### League Portfolio

Should show:

- Team build direction.
- Contention windows.
- Roster fragility.
- Positional surplus/need.
- Trade partner matching.

---

## Implementation Roadmap

### Phase 1: Data Spine Upgrade

- Create canonical identity artifacts.
- Split raw/normalized/features/app artifacts.
- Add source scorecards.
- Add conflict reports.
- Move identity guards from frontend-only logic into the spine.

### Phase 2: Source Comparison

- Build depth role comparison.
- Build injury/news comparison.
- Build value source comparison.
- Surface disagreement in the UI.

### Phase 3: Model Replacement

- Replace intrinsic v0 with validated position-specific models.
- Keep heuristic intrinsic as a fallback only.
- Add uncertainty bands and reason codes.
- Produce walk-forward reports.

### Phase 4: Revealed Preference Hardening

- Validate on real leagues.
- Persist and compare solves over time.
- Add pick discount learning.
- Add manager preference fingerprints only when sample size supports it.

### Phase 5: Active Product Mode

- Offseason: portfolio, trades, picks, rookies, value movement.
- In-season: role changes, injuries, game logs, usage lead-lag, props.
- Watchlist becomes the daily home surface.

---

## Definition Of Advanced

DWR becomes meaningfully advanced when it can say things like:

- "This WR's market is flat, but route/target role improved across two independent sources; similar profiles gained value within 6 weeks in prior seasons."
- "This league pays 18% above market for young QBs and discounts 2-for-1 depth packages, based on 37 completed trades."
- "This RB's value move is news-driven, but depth/snap data do not confirm a role change yet."
- "This pick is valued as mid-first by market, but your league's revealed trades price future picks closer to late-first unless the team projects bottom three."
- "This player is not underpriced; the model confidence is low because identity/source coverage is thin."

That is the line. Not more widgets. Better judgment.

