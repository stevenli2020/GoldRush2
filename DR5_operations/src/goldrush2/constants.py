"""Adjustable constants shared by GR2 extractors."""

# GR1 L1-006 config.yaml defines the implied-rate conversion as 100 - settlement_price.
# GR2 adds this separately configurable threshold because GR1 did not threshold signals.
POLICY_RATE_THRESHOLD_BPS = 10
POLICY_RATE_THRESHOLD_PP = POLICY_RATE_THRESHOLD_BPS / 100
