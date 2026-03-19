from __future__ import annotations

import json
from datetime import datetime, timezone

from google import genai
from google.genai.errors import ClientError, ServerError

from app.config import get_settings
from app.models import SearchResult


class AnalysisService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.client = genai.Client(api_key=self.settings.gemini_api_key) if self.settings.gemini_api_key else None

    async def generate_markdown_report(self, sector: str, search_result: SearchResult) -> str:
        if not self.client:
            return self._fallback_markdown(sector, search_result, reason="Gemini API key not configured")

        prompt = self._build_prompt(sector, search_result)
        try:
            response = await self.client.aio.models.generate_content(
                model=self.settings.gemini_model,
                contents=prompt,
            )
            text = (response.text or "").strip()
            if not text:
                return self._fallback_markdown(sector, search_result, reason="Gemini returned an empty response")
            return text
        except (ClientError, ServerError, Exception) as exc:
            return self._fallback_markdown(sector, search_result, reason=f"AI analysis unavailable: {exc}")

    def _build_prompt(self, sector: str, search_result: SearchResult) -> str:
        payload = {
            "sector": sector,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "sources": [source.model_dump() for source in search_result.sources],
        }
        return f"""
You are a financial market research analyst focused on Indian sectors.
Analyze the provided current news snippets for the sector and produce a concise markdown report.

Rules:
- Return markdown only.
- Be cautious and avoid making up facts.
- Include uncertainty when the evidence is thin.
- Focus on Indian trade opportunities, catalysts, risks, and practical watch items.
- Do not provide personalized investment advice.
- Use the exact sections below in this exact order.

Required markdown structure:
# Market Analysis Report: <Sector>
## Executive Summary
## Current Trade Opportunities
## Key Catalysts
## Risks and Headwinds
## What to Watch Next
## Source Snapshot

For "Current Trade Opportunities", give 3 to 5 bullet points with a short rationale for each.
For "Source Snapshot", provide a bullet list with title, source name, and published date if available.

Input data:
```json
{json.dumps(payload, ensure_ascii=False, indent=2)}
```
""".strip()

    def _fallback_markdown(self, sector: str, search_result: SearchResult, reason: str) -> str:
        lines = [
            f"# Market Analysis Report: {sector.title()}",
            "",
            "## Executive Summary",
            f"AI-generated analysis is currently unavailable. This fallback report summarizes the latest collected signals for the **{sector}** sector in India.",
            "",
            "## Current Trade Opportunities",
        ]
        if search_result.sources:
            for source in search_result.sources[:5]:
                lines.append(
                    f"- **{source.title}** — Potential signal based on recent coverage from *{source.source}*. Review the source before making any decision."
                )
        else:
            lines.append("- No current sources were collected, so no fresh trade opportunities could be derived.")

        lines.extend(
            [
                "",
                "## Key Catalysts",
                "- Policy changes, export demand, earnings updates, and supply-chain announcements can all move sector sentiment.",
                "",
                "## Risks and Headwinds",
                "- News coverage alone is not sufficient for decision-making.",
                "- Macro risk, regulation, and valuation changes can quickly invalidate a trade setup.",
                "",
                "## What to Watch Next",
                "- Track follow-up earnings, government notifications, export/import data, and management commentary.",
                "",
                "## Source Snapshot",
            ]
        )
        if search_result.sources:
            for source in search_result.sources[:8]:
                date_text = f" ({source.published_at})" if source.published_at else ""
                lines.append(f"- [{source.title}]({source.url}) — {source.source}{date_text}")
        else:
            lines.append("- No sources collected.")

        lines.extend(["", f"> Fallback note: {reason}"])
        return "\n".join(lines)
