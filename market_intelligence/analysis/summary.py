"""Aggregate stats computed over a set of search results (as a DataFrame)."""

import pandas as pd


def summarize_results(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "total_results": 0,
            "companies": 0,
            "countries": 0,
            "top_companies": {},
            "top_countries": {},
            "by_source_type": {},
            "avg_evidence_score": 0.0,
        }

    return {
        "total_results": len(df),
        "companies": df["company"].nunique(),
        "countries": df["country"].nunique(),
        "top_companies": df["company"].value_counts().head(10).to_dict(),
        "top_countries": df["country"].value_counts().head(10).to_dict(),
        "by_source_type": df["source_type"].value_counts().to_dict(),
        "avg_evidence_score": round(df["evidence_score"].mean(), 2),
    }


def confidence_breakdown(df: pd.DataFrame) -> dict:
    if df.empty or "confidence_label" not in df.columns:
        return {}
    return df["confidence_label"].value_counts().to_dict()
