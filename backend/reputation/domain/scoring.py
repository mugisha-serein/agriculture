"""Bayesian scoring helpers for reputation aggregation."""

MIN_RATING = 1
MAX_RATING = 5
DEFAULT_PRIOR_WEIGHT = 5.0
MAX_TRUST_BOOST = 1.5


def bayesian_average(average_rating, review_count, global_mean, prior_weight=DEFAULT_PRIOR_WEIGHT):
    """Return classical Bayesian average."""
    reviews_weight = float(review_count)
    prior = float(prior_weight)
    if reviews_weight + prior <= 0:
        return float(global_mean)
    return ((reviews_weight / (reviews_weight + prior)) * average_rating) + (
        (prior / (reviews_weight + prior)) * global_mean
    )


def weighted_bayesian_average(
    base_score,
    helpfulness_ratio=0.0,
    verified_ratio=0.0,
    reviewer_reputation=0.0,
):
    """Boost base score by trust signals capped by MAX_TRUST_BOOST."""
    trust_component = min(
        1.0,
        (helpfulness_ratio * 0.5)
        + (verified_ratio * 0.3)
        + ((reviewer_reputation / MAX_RATING) * 0.2),
    )
    boost = 1.0 + trust_component
    return min(MAX_RATING, base_score * boost)
