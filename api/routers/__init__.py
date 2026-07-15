"""Shared helpers for MarketMind API routers."""

from dataclasses import fields, is_dataclass

import pandas as pd


def to_jsonable(value):
    """Convert service DTOs and DataFrames into JSON-compatible values."""
    if is_dataclass(value):
        return {
            field.name: to_jsonable(getattr(value, field.name))
            for field in fields(value)
        }

    if isinstance(value, pd.DataFrame):
        clean_df = value.where(pd.notna(value), None)
        return clean_df.to_dict(orient="records")

    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}

    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]

    if pd.isna(value):
        return None

    return value
