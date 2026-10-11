---
name: Prediction market scope
description: The user's market preference for this project's prediction and slip output.
---

Prediction and slip output should include only Over/Under picks, with a minimum value gap of +5%. Do not include 1X2 or BTTS as recommendation candidates.

**Why:** the user explicitly wants to focus this project on Over/Under and remove 1X2 and BTTS predictions from slips.

**How to apply:** use the O/U-only scope and gap threshold for recommendation, terminal, saved-slip, and new-draft paths. Preserve existing O/U tracking history; legacy pending rows without gap metadata are for tracking, not proof of current slip eligibility.
