import pandas as pd
import numpy as np
from typing import Dict, List


def run_analytics(df: pd.DataFrame, schema: Dict) -> Dict:
    """
    Core analytics engine — category-aware.
    Runs analytics both overall and per category.
    """
    time_col      = schema["time_columns"][0]
    metric_cols   = schema["metric_columns"]
    category_cols = schema["category_columns"]

    # Parse dates and sort
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.sort_values(time_col).reset_index(drop=True)

    results = {}

    # Overall analytics (all data combined)
    results["summary"]           = compute_summary(df, metric_cols)
    results["trends"]            = compute_trends(df, time_col, metric_cols)
    results["period_comparison"] = compute_period_comparison(df, time_col, metric_cols)
    results["anomalies"]         = detect_anomalies(df, time_col, metric_cols)

    # Category-level analytics (per program/group) — most accurate
    if category_cols:
        results["category_analysis"] = compute_category_analytics(
            df, time_col, metric_cols, category_cols[0]
        )

    return results


def compute_category_analytics(
    df: pd.DataFrame,
    time_col: str,
    metric_cols: List[str],
    category_col: str
) -> Dict:
    """
    Run trend + period comparison separately for each category.
    Gives accurate per-program insights instead of mixed results.
    """
    category_results = {}

    for category in sorted(df[category_col].unique()):
        subset = df[df[category_col] == category].copy()
        subset = subset.sort_values(time_col).reset_index(drop=True)

        category_results[str(category)] = {
            "summary":           compute_summary(subset, metric_cols),
            "trends":            compute_trends(subset, time_col, metric_cols),
            "period_comparison": compute_period_comparison(subset, time_col, metric_cols),
        }

    return category_results


def compute_summary(df: pd.DataFrame, metric_cols: List[str]) -> Dict:
    """
    Compute summary statistics for each metric column.
    """
    summary = {}

    for col in metric_cols:
        series = df[col].dropna()

        if len(series) == 0:
            summary[col] = {
                "total": 0, "average": 0, "min": 0,
                "max": 0, "latest": 0, "count": 0
            }
            continue

        summary[col] = {
            "total":   round(float(series.sum()), 2),
            "average": round(float(series.mean()), 2),
            "min":     round(float(series.min()), 2),
            "max":     round(float(series.max()), 2),
            "latest":  round(float(series.iloc[-1]), 2),
            "count":   int(series.count())
        }

    return summary


def compute_trends(
    df: pd.DataFrame,
    time_col: str,
    metric_cols: List[str]
) -> Dict:
    """
    Detect trend direction for each metric using linear regression slope.
    Returns: improving / declining / stable
    """
    trends = {}

    for col in metric_cols:
        series = df[col].dropna()

        if len(series) < 2:
            trends[col] = {
                "direction":      "insufficient data",
                "slope":          0,
                "interpretation": "Not enough data to determine trend."
            }
            continue

        x     = np.arange(len(series))
        y     = series.values
        slope = float(np.polyfit(x, y, 1)[0])
        avg   = float(series.mean())

        # 2% of average = meaningful change threshold
        threshold = avg * 0.02

        if slope > threshold:
            direction      = "improving"
            interpretation = f"{col.replace('_', ' ').title()} is trending upward over time."
        elif slope < -threshold:
            direction      = "declining"
            interpretation = f"{col.replace('_', ' ').title()} is trending downward and may need attention."
        else:
            direction      = "stable"
            interpretation = f"{col.replace('_', ' ').title()} has remained relatively stable."

        trends[col] = {
            "direction":      direction,
            "slope":          round(slope, 4),
            "interpretation": interpretation
        }

    return trends


def compute_period_comparison(
    df: pd.DataFrame,
    time_col: str,
    metric_cols: List[str]
) -> Dict:
    """
    Compare latest period vs previous period.
    Returns absolute change, percentage change, and direction.
    """
    comparison = {}

    for col in metric_cols:
        series = df[[time_col, col]].dropna()

        if len(series) < 2:
            comparison[col] = {
                "latest_value":   0,
                "previous_value": 0,
                "change":         0,
                "pct_change":     0,
                "direction":      "insufficient data",
                "note":           "Not enough data to compare periods."
            }
            continue

        latest   = float(series[col].iloc[-1])
        previous = float(series[col].iloc[-2])
        change   = round(latest - previous, 2)

        if previous != 0:
            pct_change = round((change / previous) * 100, 2)
        else:
            pct_change = 0.0

        if pct_change > 5:
            direction = "up"
            note      = f"Increased by {abs(pct_change)}% compared to previous period."
        elif pct_change < -5:
            direction = "down"
            note      = f"Decreased by {abs(pct_change)}% compared to previous period."
        else:
            direction = "no significant change"
            note      = "Performance is consistent with the previous period."

        comparison[col] = {
            "latest_value":   latest,
            "previous_value": previous,
            "change":         change,
            "pct_change":     pct_change,
            "direction":      direction,
            "note":           note
        }

    return comparison


def detect_anomalies(
    df: pd.DataFrame,
    time_col: str,
    metric_cols: List[str]
) -> List[Dict]:
    """
    Flag sudden spikes or drops using Z-score method.
    Any value more than 2 standard deviations from the mean is flagged.
    """
    anomalies = []

    for col in metric_cols:
        series = df[col].dropna()

        if len(series) < 3:
            continue

        mean = series.mean()
        std  = series.std()

        if std == 0:
            continue

        for i, value in enumerate(series):
            z_score = (value - mean) / std

            if abs(z_score) > 2:
                flag_type = "spike" if z_score > 0 else "drop"
                date_val  = str(df[time_col].iloc[i].date())

                anomalies.append({
                    "metric":  col,
                    "date":    date_val,
                    "value":   round(float(value), 2),
                    "flag":    flag_type,
                    "z_score": round(float(z_score), 2),
                    "note":    f"Unusual {flag_type} detected in {col.replace('_', ' ')} on {date_val}."
                })

    return anomalies