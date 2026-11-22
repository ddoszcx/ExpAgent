from numbers import Integral

from scipy.stats import chisquare


def srm_check(n_control: int, n_treatment: int, expected_ratio: float = 0.5) -> dict:
    """Check the observed split against the planned control fraction (p < 0.001)."""
    for count in (n_control, n_treatment):
        if isinstance(count, bool) or not isinstance(count, Integral) or count < 0:
            raise ValueError("Group sizes must be non-negative integers.")
    total = int(n_control) + int(n_treatment)
    if total == 0:
        raise ValueError("At least one user is required.")
    if not 0 < expected_ratio < 1:
        raise ValueError("Expected control fraction must be between 0 and 1 (exclusive).")

    statistic, p_value = chisquare(
        f_obs=[n_control, n_treatment],
        f_exp=[total * expected_ratio, total * (1 - expected_ratio)],
    )
    p_value = float(p_value)
    is_srm = p_value < 0.001
    return {
        "test": "chi_square_goodness_of_fit",
        "chi2_statistic": round(float(statistic), 4),
        "p_value": p_value,
        "is_srm": is_srm,
        "verdict": "SRM_BROKEN" if is_srm else "SRM_OK",
    }
