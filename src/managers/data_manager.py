"""Data fetching, preparation, and enrichment."""

from typing import Optional
import pandas as pd

from ..core.gdelt_api import GdeltApiClient
from ..ui.logger import Logger


class DataManager:
    """Handles data fetching, preparation, and enrichment."""
    
    def __init__(self, api_client: GdeltApiClient, logger: Logger):
        self.api_client = api_client
        self.logger = logger
        self.timeline_df = None
        self.articles_df = None
    
    def prepare_timeline_df(self, timeline_data: pd.DataFrame, timeline_mode: str) -> pd.DataFrame:
        """Process raw timeline data into usable format."""
        df = pd.DataFrame(timeline_data)
        if df.empty:
            raise ValueError("No timeline data found for this query.")

        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
            df["date"] = df["datetime"].dt.date
        elif "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.date
        else:
            raise ValueError("Timeline response did not include a datetime or date column.")

        if timeline_mode in ("timelinevol", "timelinevolraw", "timelinetone"):
            metric_col = self._find_metric_column(df)
            daily = df.groupby("date")[metric_col].mean().reset_index()
            daily.columns = ["date", "tone" if timeline_mode == "timelinetone" else "volume"]
            return daily

        numeric_cols = [
            column for column in df.columns
            if column not in ("datetime", "date") and pd.api.types.is_numeric_dtype(df[column])
        ]
        if not numeric_cols:
            raise ValueError("No numeric timeline columns found for the selected breakdown mode.")

        grouped = df.groupby("date")[numeric_cols].sum().reset_index()
        return grouped.sort_values("date")
    
    def _find_metric_column(self, df: pd.DataFrame) -> str:
        """Find the appropriate metric column in timeline data."""
        search_columns = [
            "Average Tone", "Tone", "average_tone", "tone",
            "Volume Intensity", "volume", "Volume", "Total Articles", "Total", "total", "total_articles",
        ]
        for column in search_columns:
            if column in df.columns:
                return column

        numeric_columns = [
            column for column in df.columns
            if column not in ("datetime", "date") and pd.api.types.is_numeric_dtype(df[column])
        ]
        if numeric_columns:
            fallback = numeric_columns[0]
            self.logger.log(f"Warning: using fallback numeric column '{fallback}'.")
            return fallback

        raise ValueError("Unable to locate the timeline metric column.")
    
    def enrich_articles_with_timeline(self, articles_df: pd.DataFrame) -> None:
        """Add article count data to timeline."""
        date_column = None
        parse_format = None
        
        for column_name in ("seendate", "publish_date", "date"):
            if column_name in articles_df.columns:
                date_column = column_name
                break

        if date_column == "seendate":
            parse_format = "%Y%m%dT%H%M%SZ"

        if date_column is None:
            self.logger.log("No publish/date column found in fetched articles.")
            return

        articles_df["article_datetime"] = pd.to_datetime(
            articles_df[date_column], format=parse_format, errors="coerce"
        )
        articles_df["article_date"] = articles_df["article_datetime"].dt.date

        if articles_df["article_datetime"].notna().any():
            dates = articles_df["article_datetime"].dropna()
            self.logger.log(f"Article date range: {dates.min().date()} to {dates.max().date()} using '{date_column}' column")
        else:
            self.logger.log(f"Unable to parse article dates from '{date_column}' values.")

        if articles_df["article_date"].notna().any():
            article_counts = (
                articles_df.groupby("article_date").size().rename("n_articles").reset_index()
            )
            self.timeline_df = self.timeline_df.merge(article_counts, left_on="date", 
                                                      right_on="article_date", how="left")
            self.timeline_df["n_articles"] = self.timeline_df["n_articles"].fillna(0).astype(int)
            self.timeline_df.drop(columns=["article_date"], inplace=True)
            self.logger.log("Added n_articles counts to timeline data.")
