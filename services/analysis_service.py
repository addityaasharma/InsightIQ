import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression
from model import *
from utils.config import db
from services.huggingface_service import generate_text


def detect_target_column(df):
    priority_keywords = ["revenue", "sales", "profit", "income", "earnings", "growth"]

    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns

    for col in numeric_cols:
        col_name = col.lower()
        if any(keyword in col_name for keyword in priority_keywords):
            return col

    return numeric_cols[0] if len(numeric_cols) > 0 else None


def detect_column(dataset, file_path):
    df = pd.read_csv(file_path)
    for col in df.columns:
        dtype = str(df[col].dtype)
        is_numeric = pd.api.types.is_numeric_dtype(df[col])

        try:
            pd.to_datetime(df[col], format="mixed", dayfirst=False)
            is_date = True
        except:
            is_date = False

        column_info = DatasetColumn(
            dataset_id=dataset.id,
            column_name=col,
            data_type=dtype,
            is_numeric=is_numeric,
            is_date=is_date,
        )

        db.session.add(column_info)
    db.session.commit()
    return df


def generate_charts(dataset, df):
    charts = []
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns
    date_cols = [
        col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])
    ]
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns

    for col in categorical_cols:
        try:
            df[col] = pd.to_datetime(df[col], format="mixed", dayfirst=False)
            date_cols.append(col)
        except:
            pass

    for col in numeric_cols:
        fig = px.histogram(
            df,
            x=col,
            title=f"Distribution of {col}",
            marginal="box",  # adds a boxplot on top
            nbins=30,
            color_discrete_sequence=["#636EFA"],
        )
        fig.update_layout(bargap=0.1)
        chart = Chart(
            dataset_id=dataset.id,
            chart_type="distribution",
            chart_data=fig.to_json(),
        )
        db.session.add(chart)
        charts.append(chart)

    if len(numeric_cols) > 1:
        corr_matrix = df[numeric_cols].corr()
        fig = px.imshow(
            corr_matrix,
            text_auto=".2f",
            title="Correlation Heatmap",
            color_continuous_scale="RdBu_r",
            zmin=-1,
            zmax=1,
        )
        chart = Chart(
            dataset_id=dataset.id,
            chart_type="correlation_heatmap",
            chart_data=fig.to_json(),
        )
        db.session.add(chart)
        charts.append(chart)

    if len(numeric_cols) > 0:
        fig = px.box(
            df,
            y=list(numeric_cols),
            title="Box Plot — Spread & Outliers",
            points="outliers",  # show only outlier points
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        chart = Chart(
            dataset_id=dataset.id,
            chart_type="box_plot",
            chart_data=fig.to_json(),
        )
        db.session.add(chart)
        charts.append(chart)

    if date_cols and len(numeric_cols) > 0:
        date_col = date_cols[0]
        target_col = detect_target_column(df) or numeric_cols[0]
        df_sorted = df.sort_values(date_col)
        fig = px.line(
            df_sorted,
            x=date_col,
            y=target_col,
            title=f"{target_col} Over Time",
            markers=True,
        )
        chart = Chart(
            dataset_id=dataset.id,
            chart_type="time_series",
            chart_data=fig.to_json(),
        )
        db.session.add(chart)
        charts.append(chart)

    else:
        target_col = detect_target_column(df) or numeric_cols[0]
        fig = px.line(
            df.reset_index(),
            x="index",
            y=target_col,
            title=f"{target_col} Trend (by Row Index)",
            markers=False,
        )
        chart = Chart(
            dataset_id=dataset.id,
            chart_type="trend_line",
            chart_data=fig.to_json(),
        )
        db.session.add(chart)
        charts.append(chart)

    valid_cat_cols = [
        col
        for col in categorical_cols
        if col not in date_cols and df[col].nunique() <= 20
    ]
    if valid_cat_cols and len(numeric_cols) > 0:
        cat_col = valid_cat_cols[0]
        target_col = detect_target_column(df) or numeric_cols[0]
        df_grouped = (
            df.groupby(cat_col)[target_col]
            .sum()
            .reset_index()
            .sort_values(target_col, ascending=False)
            .head(15)  # top 15 categories max
        )
        fig = px.bar(
            df_grouped,
            x=cat_col,
            y=target_col,
            title=f"{target_col} by {cat_col}",
            color=target_col,
            color_continuous_scale="Blues",
        )
        chart = Chart(
            dataset_id=dataset.id,
            chart_type="bar_breakdown",
            chart_data=fig.to_json(),
        )
        db.session.add(chart)
        charts.append(chart)

    if len(numeric_cols) >= 2:
        target_col = detect_target_column(df) or numeric_cols[0]
        other_col = next((c for c in numeric_cols if c != target_col), numeric_cols[1])
        fig = px.scatter(
            df,
            x=other_col,
            y=target_col,
            title=f"{target_col} vs {other_col}",
            trendline="ols",  # adds a regression line
            color_discrete_sequence=["#EF553B"],
        )
        chart = Chart(
            dataset_id=dataset.id,
            chart_type="scatter_plot",
            chart_data=fig.to_json(),
        )
        db.session.add(chart)
        charts.append(chart)

    db.session.commit()
    return charts


from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split


def build_features(df, target, numeric_cols):
    """Build meaningful features from the dataframe."""
    feature_cols = [c for c in numeric_cols if c != target]
    X = pd.DataFrame()

    if feature_cols:
        X = df[feature_cols].copy()

    for lag in range(1, 4):
        X[f"{target}_lag{lag}"] = df[target].shift(lag)

    X[f"{target}_rolling_mean3"] = df[target].shift(1).rolling(3).mean()
    X[f"{target}_rolling_std3"]  = df[target].shift(1).rolling(3).std()
    X["row_index"] = np.arange(len(df))

    X = X.fillna(0)
    return X


def evaluate_model(model, X_train, X_test, y_train, y_test):
    """Train and return evaluation metrics."""
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    return {
        "mae":  round(mean_absolute_error(y_test, preds), 4),
        "rmse": round(np.sqrt(mean_squared_error(y_test, preds)), 4),
        "r2":   round(r2_score(y_test, preds), 4),
    }


def run_prediction(dataset, df):
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    if len(numeric_cols) == 0:
        return None

    target = detect_target_column(df)
    if target is None:
        return None

    X = build_features(df, target, numeric_cols)
    y = df[target]

    # Need at least 10 rows for a meaningful split
    if len(df) < 10:
        test_size = 0.1
    else:
        test_size = 0.2

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, shuffle=False
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    candidates = {
        "LinearRegression":       LinearRegression(),
        "Ridge":                  Ridge(alpha=1.0),
        "Lasso":                  Lasso(alpha=0.1, max_iter=5000),
        "RandomForest":           RandomForestRegressor(n_estimators=100, random_state=42),
        "GradientBoosting":       GradientBoostingRegressor(n_estimators=100, random_state=42),
    }

    leaderboard = {}
    for name, model in candidates.items():
        try:
            metrics = evaluate_model(
                model,
                X_train_scaled, X_test_scaled,
                y_train, y_test,
            )
            leaderboard[name] = {"model": model, "metrics": metrics}
        except Exception as e:
            print(f"Model {name} failed: {e}")

    if not leaderboard:
        return None

    best_name = max(leaderboard, key=lambda n: leaderboard[n]["metrics"]["r2"])
    best_entry = leaderboard[best_name]
    best_model = best_entry["model"]
    best_metrics = best_entry["metrics"]

    X_all_scaled = scaler.fit_transform(X)
    best_model.fit(X_all_scaled, y)

    last_row    = X.iloc[[-1]].copy()
    last_target = float(y.iloc[-1])
    forecasts   = []

    for step in range(1, 6):
        last_row["row_index"] += 1

        if f"{target}_lag3" in last_row.columns:
            last_row[f"{target}_lag3"] = last_row.get(f"{target}_lag2", last_target)
        if f"{target}_lag2" in last_row.columns:
            last_row[f"{target}_lag2"] = last_row.get(f"{target}_lag1", last_target)
        if f"{target}_lag1" in last_row.columns:
            last_row[f"{target}_lag1"] = last_target

        scaled_row = scaler.transform(last_row)
        pred_val   = float(best_model.predict(scaled_row)[0])
        forecasts.append(round(pred_val, 4))
        last_target = pred_val  # use prediction as next lag

    feature_importance = {}
    if hasattr(best_model, "feature_importances_"):
        importance_vals = best_model.feature_importances_
        feature_importance = dict(
            sorted(
                zip(X.columns.tolist(), importance_vals.tolist()),
                key=lambda x: x[1],
                reverse=True,
            )
        )

    model_comparison = {
        name: entry["metrics"]
        for name, entry in leaderboard.items()
    }

    last_actual  = float(y.iloc[-1])
    next_forecast = forecasts[0]
    change_pct   = ((next_forecast - last_actual) / last_actual * 100) if last_actual else 0

    if change_pct > 5:
        trend = "upward"
        business_signal = "Positive growth expected. Consider scaling operations."
    elif change_pct < -5:
        trend = "downward"
        business_signal = "Decline expected. Review cost controls and strategy."
    else:
        trend = "stable"
        business_signal = "Performance appears stable. Focus on optimisation."

    prediction = Prediction(
        dataset_id=dataset.id,
        model_used=best_name,
        prediction_data={
            "target_column":      target,
            "future_predictions": [
                {"step": i + 1, "value": v}
                for i, v in enumerate(forecasts)
            ],
            "model_performance": {
                "best_model": best_name,
                "metrics":    best_metrics,
                "comparison": model_comparison,
            },
            "feature_importance": feature_importance,
            "business_insight": {
                "trend":          trend,
                "change_pct":     round(change_pct, 2),
                "signal":         business_signal,
                "last_actual":    round(last_actual, 4),
                "next_forecast":  round(next_forecast, 4),
            },
        },
    )

    db.session.add(prediction)
    db.session.commit()
    return prediction.prediction_data


def generate_insights(dataset, df):
    insights = []
    numeric_cols     = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    target_col       = detect_target_column(df)

    summary_stats = df.describe().round(2).to_string()

    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_report = "\n".join(
        f"  - {col}: {missing[col]} missing ({missing_pct[col]}%)"
        for col in df.columns if missing[col] > 0
    ) or "  No missing values."

    correlation_report = ""
    if target_col and len(numeric_cols) > 1:
        corr = df[numeric_cols].corr()[target_col].drop(target_col).sort_values(ascending=False).round(3)
        correlation_report = "\n".join(
            f"  - {col}: {val}" for col, val in corr.items()
        )

    category_report = ""
    for col in categorical_cols[:3]:
        top = df[col].value_counts().head(5)
        category_report += f"\n  {col} top values:\n"
        category_report += "\n".join(f"    - {k}: {v}" for k, v in top.items())

    target_report = ""
    if target_col:
        t = df[target_col]
        growth = ((t.iloc[-1] - t.iloc[0]) / t.iloc[0] * 100) if t.iloc[0] != 0 else 0
        target_report = f"""
  Column      : {target_col}
  Total       : {round(t.sum(), 2)}
  Mean        : {round(t.mean(), 2)}
  Median      : {round(t.median(), 2)}
  Std Dev     : {round(t.std(), 2)}
  Min → Max   : {round(t.min(), 2)} → {round(t.max(), 2)}
  First→Last  : {round(float(t.iloc[0]), 2)} → {round(float(t.iloc[-1]), 2)}
  Overall Trend: {"▲ Up" if growth > 0 else "▼ Down"} {abs(round(growth, 2))}%
"""

    skew_report = ""
    if numeric_cols:
        skew = df[numeric_cols].skew().round(3)
        skew_report = "\n".join(
            f"  - {col}: skewness={val} ({'right-skewed' if val > 1 else 'left-skewed' if val < -1 else 'normal'})"
            for col, val in skew.items()
        )

    # ── Prompt ────────────────────────────────────────────────────────────────
    prompt = f"""
You are a senior business data analyst and strategic consultant.
You have been given a full analysis of a business dataset. Your job is to generate deep, specific, and actionable insights — not generic observations.

Use ONLY the data provided. Do NOT make up numbers. Be precise.

════════════════════════════════════════
DATASET OVERVIEW
════════════════════════════════════════
Rows         : {len(df)}
Columns      : {len(df.columns)}
Numeric Cols : {', '.join(numeric_cols) or 'None'}
Category Cols: {', '.join(categorical_cols) or 'None'}
Target Column: {target_col or 'Not identified'}

════════════════════════════════════════
TARGET METRIC ANALYSIS
════════════════════════════════════════
{target_report or '  No target column identified.'}

════════════════════════════════════════
STATISTICAL SUMMARY
════════════════════════════════════════
{summary_stats}

════════════════════════════════════════
MISSING DATA REPORT
════════════════════════════════════════
{missing_report}

════════════════════════════════════════
CORRELATION WITH TARGET ({target_col})
════════════════════════════════════════
{correlation_report or '  Not available.'}

════════════════════════════════════════
DISTRIBUTION & SKEWNESS
════════════════════════════════════════
{skew_report or '  Not available.'}

════════════════════════════════════════
CATEGORY BREAKDOWN
════════════════════════════════════════
{category_report or '  No categorical columns.'}

════════════════════════════════════════
YOUR ANALYSIS TASK
════════════════════════════════════════
Provide a structured analysis with the following sections.
For each point, cite specific numbers from the data above.

1. EXECUTIVE SUMMARY (2-3 sentences summarizing the overall business health)

2. KEY BUSINESS INSIGHTS (exactly 4 insights)
   - Each insight must reference a specific metric or column
   - Explain WHY it matters for the business
   - Format: [Insight title]: [Observation]. [Business implication].

3. GROWTH OPPORTUNITIES (2 specific opportunities based on the data)
   - Reference which columns/categories support this opportunity

4. RISK FLAGS (3 risks found in the data)
   - Include data quality risks (missing values, skewness) if present
   - Include business risks (declining metrics, high variance)

5. ACTIONABLE RECOMMENDATIONS (3 concrete recommendations)
   - Each must be tied to a specific finding in the data
   - Format: [Action] → [Expected outcome] → [Metric to track]

6. DATA QUALITY ASSESSMENT
   - Rate overall data quality: Excellent / Good / Fair / Poor
   - List specific issues found (missing values, skewness, outliers)
   - Suggest what additional data would improve analysis

Be specific. Be concise. Avoid filler phrases like "it is important to note".
"""

    insight_text = generate_text(prompt, max_tokens=1200)

    insight = Insight(
        dataset_id=dataset.id,
        insight_type="ai_analysis",
        insight_data={
            "text": insight_text,
            "context": {
                "target_column":    target_col,
                "rows":             len(df),
                "numeric_columns":  numeric_cols,
                "category_columns": categorical_cols,
                "missing_fields":   [col for col in df.columns if missing[col] > 0],
                "target_summary":   {
                    "total":  round(float(df[target_col].sum()), 2)  if target_col else None,
                    "mean":   round(float(df[target_col].mean()), 2) if target_col else None,
                    "trend":  ("up" if growth > 0 else "down")       if target_col else None,
                    "growth_pct": round(growth, 2)                   if target_col else None,
                },
            },
        },
    )

    db.session.add(insight)
    db.session.commit()
    insights.append(insight)
    return insights




def calculate_business_score(dataset, df):

    if "revenue" in df.columns and "cost" in df.columns:
        revenue = df["revenue"].sum()
        cost = df["cost"].sum()
        profit = revenue - cost
        profitability = profit / revenue if revenue else 0

    else:
        profitability = 0.5

    score = BusinessScore(
        dataset_id=dataset.id,
        profitability_score=profitability,
        growth_score=0.6,
        risk_score=0.3,
        recommendation="Increase marketing and reduce operational cost",
    )

    db.session.add(score)
    db.session.commit()
    return score


from scipy import stats
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import LocalOutlierFactor


def detect_anomalies(dataset, df):
    numeric_cols = df.select_dtypes(include=["int64", "float64"]).columns.tolist()
    anomalies = []

    if not numeric_cols:
        return anomalies

    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 5:
            continue

        col_anomalies = {}

        z_threshold    = 2.5 if len(series) < 50 else 3.0   # looser for small datasets
        modz_threshold = 3.0 if len(series) < 50 else 3.5
        iqr_multiplier = 1.5                                  # standard Tukey

        # ── Method 1: Z-Score ─────────────────────────────────────────────────
        z_scores      = np.abs(stats.zscore(series))
        z_outlier_idx = series.index[z_scores > z_threshold].tolist()
        col_anomalies["z_score"] = {
            "indices":   z_outlier_idx,
            "count":     len(z_outlier_idx),
            "threshold": z_threshold,
            "values":    series.loc[z_outlier_idx].round(4).tolist(),
        }

        # ── Method 2: IQR ─────────────────────────────────────────────────────
        Q1, Q3    = series.quantile(0.25), series.quantile(0.75)
        IQR       = Q3 - Q1
        iqr_lower = Q1 - iqr_multiplier * IQR
        iqr_upper = Q3 + iqr_multiplier * IQR

        # fallback: if IQR is 0 (all same values), use std-based bounds
        if IQR == 0:
            iqr_lower = series.mean() - 2 * series.std()
            iqr_upper = series.mean() + 2 * series.std()

        iqr_outlier_idx = series.index[
            (series < iqr_lower) | (series > iqr_upper)
        ].tolist()
        col_anomalies["iqr"] = {
            "indices": iqr_outlier_idx,
            "count":   len(iqr_outlier_idx),
            "lower":   round(iqr_lower, 4),
            "upper":   round(iqr_upper, 4),
            "values":  series.loc[iqr_outlier_idx].round(4).tolist(),
        }

        # ── Method 3: Modified Z-Score ────────────────────────────────────────
        median    = series.median()
        mad       = np.median(np.abs(series - median))
        mod_z     = 0.6745 * (series - median) / (mad + 1e-10)
        mod_z_idx = series.index[np.abs(mod_z) > modz_threshold].tolist()
        col_anomalies["modified_z_score"] = {
            "indices":   mod_z_idx,
            "count":     len(mod_z_idx),
            "median":    round(float(median), 4),
            "mad":       round(float(mad), 4),
            "values":    series.loc[mod_z_idx].round(4).tolist(),
        }

        # ── Method 4: Trend Deviation ─────────────────────────────────────────
        if len(series) >= 10:
            window       = min(5, len(series) // 3)          # adaptive window
            rolling_mean = series.rolling(window=window, center=True, min_periods=1).mean()
            residuals    = series - rolling_mean
            res_std      = residuals.std()
            trend_idx    = series.index[
                np.abs(residuals) > 1.5 * res_std            # looser than before (was 2)
            ].tolist()
        else:
            trend_idx = []
        col_anomalies["trend_deviation"] = {
            "indices": trend_idx,
            "count":   len(trend_idx),
            "values":  series.loc[trend_idx].round(4).tolist() if trend_idx else [],
        }

        # ── Consensus: adaptive threshold ────────────────────────────────────
        all_flagged = (
            set(z_outlier_idx)
            | set(iqr_outlier_idx)
            | set(mod_z_idx)
            | set(trend_idx)
        )

    
        if len(series) < 30:
            min_consensus = 1
        else:
            min_consensus = 2

        consensus_idx = [
            idx for idx in all_flagged
            if sum([
                idx in z_outlier_idx,
                idx in iqr_outlier_idx,
                idx in mod_z_idx,
                idx in trend_idx,
            ]) >= min_consensus
        ]

    
        scored_anomalies = []
        for idx in consensus_idx:
            val     = float(series.loc[idx])
            loc     = series.index.get_loc(idx)
            z_val   = float(np.abs(stats.zscore(series)).iloc[loc])
            methods = sum([
                idx in z_outlier_idx,
                idx in iqr_outlier_idx,
                idx in mod_z_idx,
                idx in trend_idx,
            ])
            severity = (
                "critical" if z_val > 4 or methods == 4 else
                "high"     if z_val > 3 or methods == 3 else
                "medium"
            )
            scored_anomalies.append({
                "row_index":       idx,
                "value":           round(val, 4),
                "z_score":         round(z_val, 4),
                "methods_flagged": methods,
                "severity":        severity,
                "direction":       "above_normal" if val > float(median) else "below_normal",
            })

        severity_order = {"critical": 0, "high": 1, "medium": 2}
        scored_anomalies.sort(key=lambda x: severity_order[x["severity"]])

        col_stats = {
            "mean":   round(float(series.mean()), 4),
            "median": round(float(median), 4),
            "std":    round(float(series.std()), 4),
            "min":    round(float(series.min()), 4),
            "max":    round(float(series.max()), 4),
            "q1":     round(float(Q1), 4),
            "q3":     round(float(Q3), 4),
        }


        insight = Insight(
            dataset_id=dataset.id,
            insight_type="anomaly",
            insight_data={
                "column":              col,
                "total_rows":          len(series),
                "anomaly_count":       len(consensus_idx),
                "anomaly_rate_pct":    round(len(consensus_idx) / len(series) * 100, 2),
                "column_stats":        col_stats,
                "detection_methods":   col_anomalies,
                "consensus_anomalies": scored_anomalies,
                "severity_summary": {
                    "critical": sum(1 for a in scored_anomalies if a["severity"] == "critical"),
                    "high":     sum(1 for a in scored_anomalies if a["severity"] == "high"),
                    "medium":   sum(1 for a in scored_anomalies if a["severity"] == "medium"),
                },
                "clean": len(consensus_idx) == 0,   # flag: no anomalies found
            },
        )
        db.session.add(insight)
        anomalies.append(insight)

    if len(numeric_cols) >= 2 and len(df) >= 20:
        try:
            X        = df[numeric_cols].fillna(0)
            scaler   = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            # Adaptive contamination based on dataset size
            contamination = min(0.1, max(0.01, 5 / len(df)))

            iso        = IsolationForest(contamination=contamination, random_state=42, n_estimators=100)
            iso_labels = iso.fit_predict(X_scaled)
            iso_scores = iso.decision_function(X_scaled)
            iso_idx    = np.where(iso_labels == -1)[0].tolist()

            lof        = LocalOutlierFactor(n_neighbors=min(20, len(df) - 1), contamination=contamination)
            lof_labels = lof.fit_predict(X_scaled)
            lof_scores = -lof.negative_outlier_factor_
            lof_idx    = np.where(lof_labels == -1)[0].tolist()

            if len(df) < 50:
                multi_consensus = list(set(iso_idx) | set(lof_idx))   # union
            else:
                multi_consensus = list(set(iso_idx) & set(lof_idx))   # intersection

            print(f"[anomaly] multivariate → iso={len(iso_idx)} lof={len(lof_idx)} consensus={len(multi_consensus)}")

            multi_anomalies = []
            for idx in multi_consensus:
                row = df.iloc[idx][numeric_cols].round(4).to_dict()
                multi_anomalies.append({
                    "row_index":      idx,
                    "iso_score":      round(float(iso_scores[idx]), 4),
                    "lof_score":      round(float(lof_scores[idx]), 4),
                    "feature_values": row,
                })
            multi_anomalies.sort(key=lambda x: x["iso_score"])

            insight = Insight(
                dataset_id=dataset.id,
                insight_type="anomaly",
                insight_data={
                    "column":           "__multivariate__",
                    "anomaly_count":    len(multi_consensus),
                    "anomaly_rate_pct": round(len(multi_consensus) / len(df) * 100, 2),
                    "isolation_forest": {
                        "flagged_count": len(iso_idx),
                        "indices":       iso_idx,
                    },
                    "local_outlier_factor": {
                        "flagged_count": len(lof_idx),
                        "indices":       lof_idx,
                    },
                    "consensus_anomalies": multi_anomalies,
                },
            )
            db.session.add(insight)
            anomalies.append(insight)

        except Exception as e:
            print(f"[anomaly] Multivariate detection failed: {e}")

    db.session.commit()
    return anomalies



def analyze_dataset(dataset, file_path):
    result = {}
    try:
        df = detect_column(dataset, file_path)
        result["columns"] = [
            {
                "name":       col.column_name,
                "type":       col.data_type,
                "is_numeric": col.is_numeric,
                "is_date":    col.is_date,
            }
            for col in DatasetColumn.query.filter_by(dataset_id=dataset.id).all()
        ]
    except Exception as e:
        print(f"[analyze] detect_column failed: {e}")
        return None

    try:
        charts = generate_charts(dataset, df)
        result["charts"] = [
            {"type": c.chart_type, "data": c.chart_data}
            for c in charts
        ]
    except Exception as e:
        print(f"[analyze] generate_charts failed: {e}")
        result["charts"] = []

    try:
        prediction_data = run_prediction(dataset, df)
        result["prediction"] = prediction_data  # full dict with metrics, insight, forecast
    except Exception as e:
        print(f"[analyze] run_prediction failed: {e}")
        result["prediction"] = None

    try:
        anomalies = detect_anomalies(dataset, df)
        result["anomalies"] = [a.insight_data for a in anomalies]
    except Exception as e:
        print(f"[analyze] detect_anomalies failed: {e}")
        result["anomalies"] = []

    try:
        insights = generate_insights(dataset, df)
        result["insights"] = [i.insight_data for i in insights]
    except Exception as e:
        print(f"[analyze] generate_insights failed: {e}")
        result["insights"] = []

    try:
        score = calculate_business_score(dataset, df)
        result["business_score"] = {
            "profitability":    score.profitability_score,
            "growth":           score.growth_score,
            "risk":             score.risk_score,
            "recommendation":   score.recommendation,
        }
    except Exception as e:
        print(f"[analyze] calculate_business_score failed: {e}")
        result["business_score"] = {}

    return result