# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Keyword Planner (research) tools for Google Ads API.

These tools expose the read-only KeywordPlanIdeaService so a campaign can be
researched and sized *before* it is launched: keyword ideas with estimated
search volume/competition/bid ranges, and historical metrics for a fixed
keyword list you already decided on. Unlike ads_mcp/tools/mutations/criterion.py
(which manages keywords already attached to a campaign), nothing here writes
to the account.
"""

from typing import Any

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools._ads_api import enum_types
from ads_mcp.tools._ads_api import service_types
from ads_mcp.tools.mutations.common import _get_client
from ads_mcp.tools.mutations.common import _handle_google_ads_error
from ads_mcp.tools.mutations.common import _resolve_enum
from ads_mcp.tools.reporting import format_value
from fastmcp.exceptions import ToolError
from google.ads.googleads.errors import GoogleAdsException


def _metrics_dict(metrics) -> dict[str, Any]:
  """Formats a KeywordPlanHistoricalMetrics proto into a plain dict."""
  formatted = format_value(metrics)
  return formatted if isinstance(formatted, dict) else {}


@mcp.tool()
def generate_keyword_ideas(
    customer_id: str,
    keyword_texts: list[str] | None = None,
    page_url: str | None = None,
    geo_target_constant_ids: list[int] | None = None,
    language_id: int = 1019,
    include_adult_keywords: bool = False,
    keyword_plan_network: str = "GOOGLE_SEARCH",
    login_customer_id: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
  """Generates keyword ideas with search volume, competition, and bid estimates.

  Use this BEFORE launching a campaign to research and size a keyword list.
  Pass seed keywords, a landing page URL, or both — Google expands from
  whichever seed(s) are given. At least one of keyword_texts or page_url is
  required.

  Args:
      customer_id: Google Ads customer ID (digits only).
      keyword_texts: Seed keywords to expand on (e.g., ["تحضير IELTS",
        "اختبار IELTS مجاني"]). Optional if page_url is given.
      page_url: A landing page URL to derive keyword ideas from (Google
        crawls the page content). Optional if keyword_texts is given.
      geo_target_constant_ids: Geo target constant IDs to scope search
        volume to (e.g., 2682 = Saudi Arabia). Defaults to worldwide if
        omitted.
      language_id: Language constant ID. Defaults to 1019 (Arabic). Common
        values: 1000 = English, 1019 = Arabic.
      include_adult_keywords: Whether to include adult keyword ideas.
      keyword_plan_network: GOOGLE_SEARCH or GOOGLE_SEARCH_AND_PARTNERS.
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with "results": list of {text, avg_monthly_searches, competition,
      competition_index, low_top_of_page_bid_micros,
      high_top_of_page_bid_micros, monthly_search_volumes}.
  """
  if not keyword_texts and not page_url:
    raise ToolError("Provide at least one of keyword_texts or page_url.")

  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("KeywordPlanIdeaService")

  request = service_types.GenerateKeywordIdeasRequest(
      customer_id=customer_id,
      language=f"languageConstants/{language_id}",
      geo_target_constants=[
          f"geoTargetConstants/{geo_id}"
          for geo_id in (geo_target_constant_ids or [])
      ],
      include_adult_keywords=include_adult_keywords,
      keyword_plan_network=_resolve_enum(
          enum_types.KeywordPlanNetworkEnum.KeywordPlanNetwork,
          keyword_plan_network,
          "keyword_plan_network",
      ),
  )

  if keyword_texts and page_url:
    request.keyword_and_url_seed = service_types.KeywordAndUrlSeed(
        url=page_url, keywords=keyword_texts
    )
  elif page_url:
    request.url_seed = service_types.UrlSeed(url=page_url)
  else:
    request.keyword_seed = service_types.KeywordSeed(keywords=keyword_texts)

  try:
    response = service.generate_keyword_ideas(request=request)
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  results = []
  for idea in response:
    metrics = _metrics_dict(idea.keyword_idea_metrics)
    results.append({
        "text": idea.text,
        "avg_monthly_searches": metrics.get("avg_monthly_searches"),
        "competition": metrics.get("competition"),
        "competition_index": metrics.get("competition_index"),
        "low_top_of_page_bid_micros": metrics.get(
            "low_top_of_page_bid_micros"
        ),
        "high_top_of_page_bid_micros": metrics.get(
            "high_top_of_page_bid_micros"
        ),
        "monthly_search_volumes": metrics.get("monthly_search_volumes"),
    })

  return {"results": results}


@mcp.tool()
def generate_keyword_historical_metrics(
    customer_id: str,
    keywords: list[str],
    geo_target_constant_ids: list[int] | None = None,
    language_id: int = 1019,
    keyword_plan_network: str = "GOOGLE_SEARCH",
    login_customer_id: str | None = None,
) -> dict[str, list[dict[str, Any]]]:
  """Gets historical search volume and competition for a fixed keyword list.

  Unlike generate_keyword_ideas, this does NOT expand or suggest new
  keywords — it returns metrics only for the exact keywords passed in. Use
  this to validate/size a keyword list you already decided on before
  launch.

  Args:
      customer_id: Google Ads customer ID (digits only).
      keywords: Exact keyword strings to look up (max 10,000 per call).
      geo_target_constant_ids: Geo target constant IDs to scope search
        volume to (e.g., 2682 = Saudi Arabia). Defaults to worldwide if
        omitted.
      language_id: Language constant ID. Defaults to 1019 (Arabic). Common
        values: 1000 = English, 1019 = Arabic.
      keyword_plan_network: GOOGLE_SEARCH or GOOGLE_SEARCH_AND_PARTNERS.
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with "results": list of {text, close_variants,
      avg_monthly_searches, competition, competition_index,
      low_top_of_page_bid_micros, high_top_of_page_bid_micros,
      monthly_search_volumes}.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("KeywordPlanIdeaService")

  request = service_types.GenerateKeywordHistoricalMetricsRequest(
      customer_id=customer_id,
      keywords=keywords,
      language=f"languageConstants/{language_id}",
      geo_target_constants=[
          f"geoTargetConstants/{geo_id}"
          for geo_id in (geo_target_constant_ids or [])
      ],
      keyword_plan_network=_resolve_enum(
          enum_types.KeywordPlanNetworkEnum.KeywordPlanNetwork,
          keyword_plan_network,
          "keyword_plan_network",
      ),
  )

  try:
    response = service.generate_keyword_historical_metrics(request=request)
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  results = []
  for item in response.results:
    metrics = _metrics_dict(item.keyword_metrics)
    results.append({
        "text": item.text,
        "close_variants": list(item.close_variants),
        "avg_monthly_searches": metrics.get("avg_monthly_searches"),
        "competition": metrics.get("competition"),
        "competition_index": metrics.get("competition_index"),
        "low_top_of_page_bid_micros": metrics.get(
            "low_top_of_page_bid_micros"
        ),
        "high_top_of_page_bid_micros": metrics.get(
            "high_top_of_page_bid_micros"
        ),
        "monthly_search_volumes": metrics.get("monthly_search_volumes"),
    })

  return {"results": results}
