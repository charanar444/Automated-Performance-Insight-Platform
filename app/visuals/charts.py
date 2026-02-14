import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List
import json


def fig_to_clean_json(fig) -> Dict:
    """
    Convert Plotly figure to JSON with plain numeric arrays.
    Prevents binary encoding (bdata) issue in the browser.
    """
    raw = json.loads(fig.to_json())

    # Walk through all data traces and convert any encoded arrays
    for trace in raw.get("data", []):
        for key in ["x", "y"]:
            val = trace.get(key)
            # If it's a dict with bdata, it's binary encoded — replace with empty
            # The actual fix is to pass plain Python lists directly
            if isinstance(val, dict) and "bdata" in val:
                trace[key] = []

    return raw


def generate_charts(df: pd.DataFrame, schema: Dict) -> Dict:
    """
    Generate all chart data for the dashboard.
    """
    time_col = schema["time_columns"][0]
    metric_cols = schema["metric_columns"]
    category_cols = schema["category_columns"]

    # Parse dates
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.sort_values(time_col).reset_index(drop=True)

    # Format dates as strings for JSON
    df["_date_str"] = df[time_col].dt.strftime("%Y-%m-%d")

    charts = {}

    charts["trend_charts"] = generate_trend_charts(
        df, "_date_str", metric_cols, category_cols
    )

    if category_cols:
        charts["category_charts"] = generate_category_charts(
            df, metric_cols, category_cols
        )

    charts["kpi_cards"] = generate_kpi_cards(df, metric_cols)

    return charts


def generate_trend_charts(
    df: pd.DataFrame,
    date_col: str,
    metric_cols: List[str],
    category_cols: List[str]
) -> List[Dict]:
    """
    Generate one line chart per metric with plain numeric arrays.
    """
    trend_charts = []

    for metric in metric_cols:
        fig = go.Figure()

        if category_cols:
            category_col = category_cols[0]
            for category in sorted(df[category_col].unique()):
                subset = df[df[category_col] == category].copy()

                # Force plain Python lists — prevents binary encoding
                x_vals = subset[date_col].tolist()
                y_vals = [float(v) for v in subset[metric].tolist()]

                fig.add_trace(go.Scatter(
                    x=x_vals,
                    y=y_vals,
                    mode="lines+markers",
                    name=str(category),
                    line=dict(width=2),
                    marker=dict(size=6)
                ))
        else:
            x_vals = df[date_col].tolist()
            y_vals = [float(v) for v in df[metric].tolist()]

            fig.add_trace(go.Scatter(
                x=x_vals,
                y=y_vals,
                mode="lines+markers",
                name=metric,
                line=dict(color="#2563EB", width=2),
                marker=dict(size=6)
            ))

        fig.update_layout(
            title=f"{metric.replace('_', ' ').title()} Over Time",
            xaxis_title="Date",
            yaxis_title=metric.replace("_", " ").title(),
            legend_title="Category",
            template="plotly_white",
            height=400,
            margin=dict(l=40, r=40, t=60, b=40)
        )

        trend_charts.append({
            "metric": metric,
            "chart_type": "line",
            "chart_json": json.loads(fig.to_json())
        })

    return trend_charts


def generate_category_charts(
    df: pd.DataFrame,
    metric_cols: List[str],
    category_cols: List[str]
) -> List[Dict]:
    """
    Generate bar charts with plain numeric arrays.
    """
    category_charts = []
    category_col = category_cols[0]

    for metric in metric_cols:
        grouped = (
            df.groupby(category_col)[metric]
            .mean()
            .round(2)
            .reset_index()
        )

        # Force plain Python lists
        x_vals = grouped[category_col].tolist()
        y_vals = [float(v) for v in grouped[metric].tolist()]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=x_vals,
            y=y_vals,
            marker_color=["#2563EB", "#16a34a", "#dc2626", "#f59e0b", "#8b5cf6"],
            text=[str(v) for v in y_vals],
            textposition="outside"
        ))

        fig.update_layout(
            title=f"Average {metric.replace('_', ' ').title()} by {category_col.replace('_', ' ').title()}",
            xaxis_title=category_col.replace("_", " ").title(),
            yaxis_title=metric.replace("_", " ").title(),
            template="plotly_white",
            height=400,
            margin=dict(l=40, r=40, t=60, b=40),
            showlegend=False
        )

        category_charts.append({
            "metric": metric,
            "chart_type": "bar",
            "chart_json": json.loads(fig.to_json())
        })

    return category_charts


def generate_kpi_cards(
    df: pd.DataFrame,
    metric_cols: List[str]
) -> List[Dict]:
    """
    Generate KPI summary card data for each metric.
    """
    kpi_cards = []

    for metric in metric_cols:
        series = df[metric].dropna()

        if len(series) < 2:
            pct_change = 0.0
        else:
            latest   = float(series.iloc[-1])
            previous = float(series.iloc[-2])
            pct_change = round(((latest - previous) / previous) * 100, 2) if previous != 0 else 0.0

        kpi_cards.append({
            "metric": metric,
            "label": metric.replace("_", " ").title(),
            "latest": round(float(series.iloc[-1]), 2),
            "average": round(float(series.mean()), 2),
            "total": round(float(series.sum()), 2),
            "min": round(float(series.min()), 2),
            "max": round(float(series.max()), 2),
            "pct_change_from_previous": pct_change,
            "trend": "up" if pct_change > 0 else "down" if pct_change < 0 else "stable"
        })

    return kpi_cards