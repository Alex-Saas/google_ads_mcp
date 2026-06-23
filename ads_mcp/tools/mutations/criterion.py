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

"""Criterion mutation tools for Google Ads API."""

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools._ads_api import common_types
from ads_mcp.tools._ads_api import enum_types
from ads_mcp.tools._ads_api import resource_types
from ads_mcp.tools._ads_api import service_types
from ads_mcp.tools.mutations.common import _get_client
from ads_mcp.tools.mutations.common import _handle_google_ads_error
from ads_mcp.tools.mutations.common import _resolve_enum
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2


@mcp.tool()
def create_keywords(
    customer_id: str,
    ad_group_resource_name: str,
    keywords: list[dict[str, str]],
    login_customer_id: str | None = None,
) -> dict[str, list[str]]:
  """Creates keywords in an ad group.

  Args:
      customer_id: Google Ads customer ID (digits only).
      ad_group_resource_name: Resource name from create_ad_group.
      keywords: List of keyword dicts, each with: - text: The keyword text
        (e.g., "ielts test preparation") - match_type: EXACT, PHRASE, or
        BROAD
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with list of created keyword resource_names.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("AdGroupCriterionService")

  operations = []
  for kw in keywords:
    match_type = _resolve_enum(
        enum_types.KeywordMatchTypeEnum.KeywordMatchType,
        kw["match_type"],
        "match_type",
    )

    criterion = resource_types.AdGroupCriterion(
        ad_group=ad_group_resource_name,
        status=(
            enum_types.AdGroupCriterionStatusEnum.AdGroupCriterionStatus.ENABLED
        ),
        keyword=common_types.KeywordInfo(
            text=kw["text"], match_type=match_type
        ),
    )
    operations.append(
        service_types.AdGroupCriterionOperation(create=criterion)
    )

  try:
    response = service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=operations
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  return {"resource_names": [r.resource_name for r in response.results]}


@mcp.tool()
def create_negative_campaign_keywords(
    customer_id: str,
    campaign_resource_name: str,
    keywords: list[str],
    login_customer_id: str | None = None,
) -> dict[str, list[str]]:
  """Creates negative keywords at the campaign level.

  Args:
      customer_id: Google Ads customer ID (digits only).
      campaign_resource_name: Resource name from create_search_campaign.
      keywords: List of negative keyword strings (e.g., ["free", "fake",
        "replica"]).
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with list of created criterion resource_names.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("CampaignCriterionService")

  operations = []
  for kw_text in keywords:
    criterion = resource_types.CampaignCriterion(
        campaign=campaign_resource_name,
        negative=True,
        keyword=common_types.KeywordInfo(
            text=kw_text,
            match_type=enum_types.KeywordMatchTypeEnum.KeywordMatchType.BROAD,
        ),
    )
    operations.append(
        service_types.CampaignCriterionOperation(create=criterion)
    )

  try:
    response = service.mutate_campaign_criteria(
        customer_id=customer_id, operations=operations
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  return {"resource_names": [r.resource_name for r in response.results]}


@mcp.tool()
def update_keyword_status(
    customer_id: str,
    ad_group_criterion_resource_name: str,
    status: str,
    login_customer_id: str | None = None,
) -> dict[str, str]:
  """Updates a keyword's status (enable or pause).

  Args:
      customer_id: Google Ads customer ID (digits only).
      ad_group_criterion_resource_name: Full resource name of the keyword
        criterion (e.g., "customers/123/adGroupCriteria/456~789").
      status: New status: ENABLED or PAUSED.
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with the updated criterion resource_name.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("AdGroupCriterionService")

  criterion = resource_types.AdGroupCriterion(
      resource_name=ad_group_criterion_resource_name,
      status=_resolve_enum(
          enum_types.AdGroupCriterionStatusEnum.AdGroupCriterionStatus,
          status,
          "status",
      ),
  )

  operation = service_types.AdGroupCriterionOperation(update=criterion)
  operation.update_mask.CopyFrom(field_mask_pb2.FieldMask(paths=["status"]))

  try:
    response = service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  return {"resource_name": response.results[0].resource_name}


@mcp.tool()
def update_keyword_bid(
    customer_id: str,
    ad_group_criterion_resource_name: str,
    cpc_bid_micros: int,
    login_customer_id: str | None = None,
) -> dict[str, str]:
  """Updates a keyword's CPC bid.

  Args:
      customer_id: Google Ads customer ID (digits only).
      ad_group_criterion_resource_name: Full resource name of the keyword
        criterion (e.g., "customers/123/adGroupCriteria/456~789").
      cpc_bid_micros: New max CPC bid in micros (e.g., 1500000 = $1.50).
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with the updated criterion resource_name.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("AdGroupCriterionService")

  criterion = resource_types.AdGroupCriterion(
      resource_name=ad_group_criterion_resource_name,
      cpc_bid_micros=cpc_bid_micros,
  )

  operation = service_types.AdGroupCriterionOperation(update=criterion)
  operation.update_mask.CopyFrom(
      field_mask_pb2.FieldMask(paths=["cpc_bid_micros"])
  )

  try:
    response = service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  return {"resource_name": response.results[0].resource_name}


@mcp.tool()
def remove_keyword(
    customer_id: str,
    ad_group_id: str,
    criterion_id: str,
    login_customer_id: str | None = None,
) -> dict[str, str]:
  """Removes a keyword from an ad group.

  Args:
      customer_id: Google Ads customer ID (digits only).
      ad_group_id: Ad group ID (digits only).
      criterion_id: Keyword criterion ID to remove (digits only).
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with the removed resource_name.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("AdGroupCriterionService")

  resource_name = service.ad_group_criterion_path(
      customer_id, ad_group_id, criterion_id
  )
  operation = service_types.AdGroupCriterionOperation(remove=resource_name)

  try:
    response = service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  return {"removed": response.results[0].resource_name}


@mcp.tool()
def create_geo_targeting(
    customer_id: str,
    campaign_resource_name: str,
    geo_target_constant_ids: list[int],
    login_customer_id: str | None = None,
) -> dict[str, list[str]]:
  """Adds location targeting to a campaign.

  Args:
      customer_id: Google Ads customer ID (digits only).
      campaign_resource_name: Resource name from create_search_campaign.
      geo_target_constant_ids: List of geo target constant IDs. Common values:
        2682 (Saudi Arabia), 2840 (United States).
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with list of created criterion resource_names.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("CampaignCriterionService")
  geo_svc = ads_client.get_service("GeoTargetConstantService")

  operations = []
  for geo_id in geo_target_constant_ids:
    resource_name = geo_svc.geo_target_constant_path(geo_id)
    criterion = resource_types.CampaignCriterion(
        campaign=campaign_resource_name,
        location=common_types.LocationInfo(
            geo_target_constant=resource_name,
        ),
    )
    operations.append(
        service_types.CampaignCriterionOperation(create=criterion)
    )

  try:
    response = service.mutate_campaign_criteria(
        customer_id=customer_id, operations=operations
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  return {"resource_names": [r.resource_name for r in response.results]}


@mcp.tool()
def remove_campaign_criterion(
    customer_id: str,
    campaign_id: str,
    criterion_id: str,
    login_customer_id: str | None = None,
) -> dict[str, str]:
  """Removes a campaign criterion (e.g., a geo target).

  Args:
      customer_id: Google Ads customer ID (digits only).
      campaign_id: Campaign ID (digits only).
      criterion_id: Criterion ID to remove (digits only).
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with the removed resource_name.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("CampaignCriterionService")

  resource_name = service.campaign_criterion_path(
      customer_id, campaign_id, criterion_id
  )
  operation = service_types.CampaignCriterionOperation(remove=resource_name)

  try:
    response = service.mutate_campaign_criteria(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  return {"removed": response.results[0].resource_name}


@mcp.tool()
def exclude_geo_targets(
    customer_id: str,
    campaign_resource_name: str,
    geo_target_constant_ids: list[int],
    login_customer_id: str | None = None,
) -> dict[str, list[str]]:
  """Excludes locations from a campaign (negative geo targeting).

  Args:
      customer_id: Google Ads customer ID (digits only).
      campaign_resource_name: Resource name from create_search_campaign.
      geo_target_constant_ids: List of geo target constant IDs to exclude.
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with list of created exclusion resource_names.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("CampaignCriterionService")
  geo_svc = ads_client.get_service("GeoTargetConstantService")

  operations = []
  for geo_id in geo_target_constant_ids:
    resource_name = geo_svc.geo_target_constant_path(geo_id)
    criterion = resource_types.CampaignCriterion(
        campaign=campaign_resource_name,
        negative=True,
        location=common_types.LocationInfo(
            geo_target_constant=resource_name,
        ),
    )
    operations.append(
        service_types.CampaignCriterionOperation(create=criterion)
    )

  try:
    response = service.mutate_campaign_criteria(
        customer_id=customer_id, operations=operations
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  return {"resource_names": [r.resource_name for r in response.results]}
