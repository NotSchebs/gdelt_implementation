import pandas as pd
from gdeltdoc import GdeltDoc, Filters
from gdeltdoc.errors import RateLimitError


class GdeltApiClient:
    def __init__(self):
        self._gd = GdeltDoc()

    def fetch_timeline(self, keyword: str, start_date: str, end_date: str, mode: str,
                       countries: list | None = None, languages: list | None = None) -> pd.DataFrame:
        filters = Filters(keyword=keyword, start_date=start_date, end_date=end_date,
                          country=countries or None, language=languages or None)
        return self._gd.timeline_search(mode, filters)

    def fetch_articles(self, keyword: str, start_date: str, end_date: str, num_records: int = 250,
                       countries: list | None = None, languages: list | None = None) -> pd.DataFrame:
        filters = Filters(
            keyword=keyword,
            start_date=start_date,
            end_date=end_date,
            num_records=num_records,
            country=countries or None,
            language=languages or None,
        )
        return self._gd.article_search(filters)
