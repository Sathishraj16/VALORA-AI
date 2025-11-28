"""
VALORA Utility Functions - Statistics
"""

import numpy as np
from typing import List, Tuple, Union, Optional
from dataclasses import dataclass


@dataclass
class StatisticalSummary:
    """Statistical summary of a dataset."""
    mean: float
    median: float
    std: float
    min: float
    max: float
    q25: float
    q75: float
    count: int


def calculate_confidence_interval(
    data: Union[List[float], np.ndarray],
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence interval for a dataset.
    
    Args:
        data: Array of values
        confidence: Confidence level (default: 0.95 for 95% CI)
    
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    data = np.array(data)
    n = len(data)
    mean = np.mean(data)
    std_err = np.std(data, ddof=1) / np.sqrt(n)
    
    # Z-scores for common confidence levels
    z_scores = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576,
    }
    
    z = z_scores.get(confidence, 1.96)
    margin = z * std_err
    
    return (mean - margin, mean + margin)


def exponential_smoothing(
    data: Union[List[float], np.ndarray],
    alpha: float = 0.3
) -> np.ndarray:
    """
    Apply exponential smoothing to a time series.
    
    Args:
        data: Time series data
        alpha: Smoothing factor (0 < alpha < 1)
    
    Returns:
        Smoothed time series
    """
    data = np.array(data)
    result = np.zeros_like(data, dtype=float)
    result[0] = data[0]
    
    for i in range(1, len(data)):
        result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
    
    return result


def moving_average(
    data: Union[List[float], np.ndarray],
    window: int = 5
) -> np.ndarray:
    """
    Calculate moving average of a time series.
    
    Args:
        data: Time series data
        window: Window size for averaging
    
    Returns:
        Moving average series
    """
    data = np.array(data)
    weights = np.ones(window) / window
    return np.convolve(data, weights, mode='valid')


def calculate_volatility(
    data: Union[List[float], np.ndarray],
    window: int = 20
) -> np.ndarray:
    """
    Calculate rolling volatility (standard deviation).
    
    Args:
        data: Time series data
        window: Window size
    
    Returns:
        Rolling volatility series
    """
    data = np.array(data)
    result = np.zeros(len(data) - window + 1)
    
    for i in range(len(result)):
        result[i] = np.std(data[i:i + window], ddof=1)
    
    return result


def calculate_returns(
    data: Union[List[float], np.ndarray],
    log_returns: bool = False
) -> np.ndarray:
    """
    Calculate period-over-period returns.
    
    Args:
        data: Price or value series
        log_returns: If True, calculate log returns
    
    Returns:
        Returns series
    """
    data = np.array(data)
    
    if log_returns:
        return np.diff(np.log(data))
    else:
        return np.diff(data) / data[:-1]


def calculate_correlation_matrix(
    data: dict[str, List[float]]
) -> dict[str, dict[str, float]]:
    """
    Calculate correlation matrix for multiple series.
    
    Args:
        data: Dictionary of series names to values
    
    Returns:
        Correlation matrix as nested dictionary
    """
    import pandas as pd
    
    df = pd.DataFrame(data)
    corr = df.corr()
    
    return corr.to_dict()


def calculate_statistics(
    data: Union[List[float], np.ndarray]
) -> StatisticalSummary:
    """
    Calculate comprehensive statistics for a dataset.
    
    Args:
        data: Array of values
    
    Returns:
        StatisticalSummary object
    """
    data = np.array(data)
    
    return StatisticalSummary(
        mean=float(np.mean(data)),
        median=float(np.median(data)),
        std=float(np.std(data, ddof=1)),
        min=float(np.min(data)),
        max=float(np.max(data)),
        q25=float(np.percentile(data, 25)),
        q75=float(np.percentile(data, 75)),
        count=len(data)
    )


def calculate_gini_coefficient(
    data: Union[List[float], np.ndarray]
) -> float:
    """
    Calculate Gini coefficient for inequality measurement.
    
    Args:
        data: Array of values (e.g., incomes, wealth)
    
    Returns:
        Gini coefficient (0 = perfect equality, 1 = perfect inequality)
    """
    data = np.array(data)
    data = np.sort(data)
    n = len(data)
    
    if n == 0:
        return 0.0
    
    # Calculate Gini using the formula: G = (2 * sum(i * x_i)) / (n * sum(x_i)) - (n + 1) / n
    index = np.arange(1, n + 1)
    return float((2 * np.sum(index * data)) / (n * np.sum(data)) - (n + 1) / n)


def calculate_herfindahl_index(
    market_shares: Union[List[float], np.ndarray]
) -> float:
    """
    Calculate Herfindahl-Hirschman Index for market concentration.
    
    Args:
        market_shares: List of market shares (should sum to 1)
    
    Returns:
        HHI value (0 to 1, higher = more concentrated)
    """
    shares = np.array(market_shares)
    return float(np.sum(shares ** 2))


def monte_carlo_simulation(
    func: callable,
    params: dict,
    n_simulations: int = 1000,
    param_distributions: Optional[dict] = None
) -> Tuple[np.ndarray, StatisticalSummary]:
    """
    Run Monte Carlo simulation.
    
    Args:
        func: Function to simulate
        params: Base parameters
        n_simulations: Number of simulation runs
        param_distributions: Optional parameter distributions for stochastic inputs
    
    Returns:
        Tuple of (results array, statistics summary)
    """
    results = []
    
    for _ in range(n_simulations):
        sim_params = params.copy()
        
        if param_distributions:
            for key, dist in param_distributions.items():
                if key in sim_params:
                    # Apply random variation based on distribution type
                    if dist["type"] == "normal":
                        sim_params[key] = np.random.normal(
                            sim_params[key],
                            dist.get("std", sim_params[key] * 0.1)
                        )
                    elif dist["type"] == "uniform":
                        sim_params[key] = np.random.uniform(
                            dist.get("min", sim_params[key] * 0.9),
                            dist.get("max", sim_params[key] * 1.1)
                        )
        
        result = func(**sim_params)
        results.append(result)
    
    results_array = np.array(results)
    stats = calculate_statistics(results_array)
    
    return results_array, stats


def bootstrap_confidence_interval(
    data: Union[List[float], np.ndarray],
    statistic: callable = np.mean,
    n_bootstrap: int = 1000,
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate bootstrap confidence interval.
    
    Args:
        data: Sample data
        statistic: Statistic function to compute
        n_bootstrap: Number of bootstrap samples
        confidence: Confidence level
    
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    data = np.array(data)
    n = len(data)
    
    bootstrap_stats = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=n, replace=True)
        bootstrap_stats.append(statistic(sample))
    
    alpha = 1 - confidence
    lower = np.percentile(bootstrap_stats, alpha / 2 * 100)
    upper = np.percentile(bootstrap_stats, (1 - alpha / 2) * 100)
    
    return (float(lower), float(upper))
