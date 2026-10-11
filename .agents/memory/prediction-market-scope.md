---
name: Prediction market scope
description: The user's market preference for this project's prediction and slip output.
---

Prediction and slip output should include only Over/Under picks. Estimate home and away scoring from each team's recent venue-specific form (roughly 8–12 matches), using xG/xGA only when consistent and otherwise goals plus shot opportunities. Keep H2H as a low-weight input.

Model total goals with Poisson and compare to no-vig market probabilities. Asian O/U evaluation must use settlement-weighted expected return, including half wins/losses and pushes. Backtests must be chronological, exclude same-day results, and report calibration and settled returns by line, odds range, league, and candidate gap. The +5 percentage-point gap is an initial threshold to validate, not a proven rule.

**Why:** the user explicitly wants O/U-only predictions, venue-specific form rather than H2H-led picks, margin-free market comparison, and evidence from leakage-free backtests before trusting the gap threshold.

**How to apply:** keep recommendation, terminal, saved-slip, and new-draft paths O/U-only; preserve existing O/U tracking history. Never treat same-day results as pre-match inputs or describe +5 pp as validated. Legacy pending rows without gap metadata are for tracking, not proof of current slip eligibility.
