"""Search operations and threading."""

import threading
import time
from typing import Callable, Tuple

import pandas as pd

from ..core.gdelt_api import GdeltApiClient
from .data_manager import DataManager
from ..ui.logger import Logger
from ..ui.dialog_manager import DialogManager


class SearchManager:
    """Handles search operations and threading."""
    
    def __init__(self, api_client: GdeltApiClient, data_manager: DataManager, 
                 logger: Logger, dialog_manager: DialogManager):
        self.api_client = api_client
        self.data_manager = data_manager
        self.logger = logger
        self.dialog_manager = dialog_manager
        self.stop_event = threading.Event()
        self.is_fetching = False
    
    def start_fetch(self, keyword: str, start_date: str, end_date: str, 
                   timeline_mode: str, fetch_articles: bool, 
                   on_finished: Callable) -> None:
        """Start data fetching in background thread."""
        self.stop_event.clear()
        self.is_fetching = True
        args = (keyword, start_date, end_date, timeline_mode, fetch_articles, on_finished)
        threading.Thread(target=self._fetch_data, args=args, daemon=True).start()
    
    def _fetch_data(self, keyword: str, start_date: str, end_date: str, 
                   timeline_mode: str, fetch_articles: bool, on_finished: Callable) -> None:
        """Internal method to fetch data."""
        try:
            if self.stop_event.is_set():
                on_finished(False, "Search stopped by user.")
                return

            self._sleep_before_request(15, "timeline")
            self.logger.log(f"Calling GDELT API for {timeline_mode} data (this may take a while)...")
            timeline_data = self.api_client.fetch_timeline(keyword, start_date, end_date, timeline_mode)

            if self.stop_event.is_set():
                on_finished(False, "Search stopped by user.")
                return

            self.data_manager.timeline_df = self.data_manager.prepare_timeline_df(timeline_data, timeline_mode)

            if fetch_articles:
                self._fetch_articles(keyword, start_date, end_date, on_finished)
            else:
                on_finished(True, "Timeline successfully fetched and processed.")

        except Exception as error:
            self._handle_error(f"An error occurred while fetching timeline data: {str(error)}", 
                             self._fetch_data, (keyword, start_date, end_date, timeline_mode, fetch_articles, on_finished),
                             False, None, on_finished)
    
    def _fetch_articles(self, keyword: str, start_date: str, end_date: str, 
                       on_finished: Callable) -> None:
        """Fetch articles after timeline."""
        if self.stop_event.is_set():
            on_finished(False, "Search stopped by user.")
            return

        try:
            self._sleep_before_request(20, "article list")
            self.logger.log("Calling GDELT API for article list (this may take a while)...")
            articles = self.api_client.fetch_articles(keyword, start_date, end_date)

            if self.stop_event.is_set():
                on_finished(False, "Search stopped by user.")
                return

            if articles is None or articles.empty:
                self.data_manager.articles_df = pd.DataFrame()
                on_finished(True, "Timeline fetched successfully, but no articles were returned.")
                return
            # Apply article-level filters if present
            filtered = self._apply_filters_to_articles(articles.copy())
            self.data_manager.articles_df = filtered
            self.data_manager.enrich_articles_with_timeline(self.data_manager.articles_df)
            on_finished(True, "Timeline and article list fetched successfully.")

        except Exception as error:
            self._handle_error(f"An error occurred while fetching articles: {str(error)}", 
                             self._fetch_articles, (keyword, start_date, end_date, on_finished),
                             True, "Timeline fetched; article retrieval cancelled due to an error.", on_finished)
    
    def _handle_error(self, message: str, callback: Callable, args: Tuple, 
                     cancel_success: bool, cancel_msg: str, 
                     on_finished: Callable) -> None:
        """Handle API errors with retry dialog."""
        self.dialog_manager.show_error_dialog(
                message,
                callback,
                args,
                cancel_success,
                cancel_msg,
                self.stop_event,
            )
    
    def _sleep_before_request(self, seconds: int, request_type: str) -> None:
        """Sleep before API request with stop check."""
        self.logger.log(f"Sleeping {seconds} seconds before sending the {request_type} request...")
        for _ in range(seconds):
            if self.stop_event.is_set():
                self.logger.log("Request cancelled before sending.")
                return
            time.sleep(1)

    def _apply_filters_to_articles(self, articles_df: pd.DataFrame) -> pd.DataFrame:
        """Filter articles DataFrame in-place based on `self.filters` if provided.

        Expected filters format: {'countries': [ISO,...], 'languages': [code,...]}
        """
        filters = getattr(self, 'filters', None)
        if not filters:
            return articles_df

        df = articles_df

        # Country filtering - try common column names
        country_codes = [c.upper() for c in filters.get('countries', []) if c]
        if country_codes:
            country_cols = [c for c in df.columns if c.lower() in ('sourcecountry', 'source_country', 'country', 'countrycode', 'iso')]
            if country_cols:
                combined = pd.Series([False] * len(df))
                for col in country_cols:
                    combined = combined | df[col].astype(str).str.upper().isin(country_codes)
                df = df[combined]
            else:
                # try searching in any string column for country ISO or name
                combined = pd.Series([False] * len(df))
                for col in df.select_dtypes(include=['object']):
                    combined = combined | df[col].astype(str).str.upper().isin(country_codes)
                df = df[combined]

        # Language filtering - common column names
        lang_codes = [l.lower() for l in filters.get('languages', []) if l]
        if lang_codes:
            lang_cols = [c for c in df.columns if c.lower() in ('language', 'lang', 'languagecode')]
            if lang_cols:
                combined = pd.Series([False] * len(df))
                for col in lang_cols:
                    combined = combined | df[col].astype(str).str.lower().isin(lang_codes)
                df = df[combined]
            else:
                # try searching any string column
                combined = pd.Series([False] * len(df))
                for col in df.select_dtypes(include=['object']):
                    combined = combined | df[col].astype(str).str.lower().isin(lang_codes)
                df = df[combined]

        self.logger.log(f"Applied filters: countries={len(country_codes)}, languages={len(lang_codes)}; resulting articles={len(df)}")
        return df
