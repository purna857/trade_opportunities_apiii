from __future__ import annotations

import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.models import MarketSource, SearchResult


class MarketSearchService:
    GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

    async def collect_sector_news(self, sector: str) -> SearchResult:
        settings = get_settings()
        query = f"India {sector} sector market trade opportunities OR exports OR growth OR regulation"
        params = {"q": query, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"}

        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds, follow_redirects=True) as client:
            response = await client.get(self.GOOGLE_NEWS_RSS, params=params)
            response.raise_for_status()

        sources = self._parse_google_news_rss(response.text)[: settings.max_search_results]
        return SearchResult(sector=sector, query=query, sources=sources)

    def _parse_google_news_rss(self, xml_text: str) -> list[MarketSource]:
        root = ET.fromstring(xml_text)
        items = root.findall("./channel/item")
        parsed: list[MarketSource] = []

        for item in items:
            title = self._clean_text(item.findtext("title", default="Untitled"))
            link = item.findtext("link", default="")
            description = self._clean_text(item.findtext("description", default=""))
            pub_date = item.findtext("pubDate", default=None)
            source_name = "Google News"
            source_tag = item.find("source")
            if source_tag is not None and source_tag.text:
                source_name = source_tag.text.strip()

            parsed.append(
                MarketSource(
                    title=title,
                    url=link,
                    snippet=description,
                    source=source_name,
                    published_at=self._normalize_datetime(pub_date),
                )
            )
        return parsed

    def _clean_text(self, value: str) -> str:
        value = html.unescape(value)
        value = re.sub(r"<[^>]+>", " ", value)
        value = re.sub(r"\s+", " ", value).strip()
        return value

    def _normalize_datetime(self, value: str | None) -> str | None:
        if not value:
            return None
        try:
            dt = datetime.strptime(value, "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
            return dt.isoformat()
        except ValueError:
            return value
