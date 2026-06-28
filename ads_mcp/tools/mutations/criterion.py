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
from fastmcp.exceptions import ToolError
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


@mcp.tool()
def update_keyword_final_url(
    customer_id: str,
    ad_group_criterion_resource_name: str,
    final_url: str,
    login_customer_id: str | None = None,
) -> dict[str, str]:
  """Sets or updates a keyword's final URL (keyword-level destination override).

  Keyword-level final URLs override the ad-level final URL for this specific
  keyword, allowing different landing pages per keyword without creating
  separate ads.

  Args:
      customer_id: Google Ads customer ID (digits only).
      ad_group_criterion_resource_name: Full resource name of the keyword
        criterion (e.g., "customers/123/adGroupCriteria/456~789").
      final_url: The destination URL for this keyword (e.g.,
        "https://goielts.ai/lp/ielts-writing/?kw=ielts+writing+test").
        Must use HTTPS. Pass empty string to clear the keyword-level URL
        and fall back to the ad-level final URL.
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with the updated criterion resource_name.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("AdGroupCriterionService")

  criterion = resource_types.AdGroupCriterion(
      resource_name=ad_group_criterion_resource_name,
  )
  if final_url:
    criterion.final_urls.append(final_url)

  operation = service_types.AdGroupCriterionOperation(update=criterion)
  operation.update_mask.CopyFrom(
      field_mask_pb2.FieldMask(paths=["final_urls"])
  )

  try:
    response = service.mutate_ad_group_criteria(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  return {"resource_name": response.results[0].resource_name}


@mcp.tool()
def create_image_asset(
    customer_id: str,
    name: str,
    image_url: str,
    login_customer_id: str | None = None,
) -> dict[str, str]:
  """Creates an image asset from a public URL (first step for image extensions).

  Downloads the image from the URL and uploads it as a Google Ads image asset.
  After creation, use add_image_extension_to_campaign to link it to a campaign.

  Args:
      customer_id: Google Ads customer ID (digits only).
      name: A descriptive name for the image asset (e.g., "GoIELTS Hero Banner").
      image_url: Public URL of the image to upload. Requirements for image
        extensions: JPEG or PNG, minimum 300x300px, maximum 5120x5120px,
        max file size 5MB. Landscape ratio (1.91:1) recommended.
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with the created asset resource_name (use this in
      add_image_extension_to_campaign).
  """
  import urllib.request as _url_req

  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("AssetService")

  with _url_req.urlopen(image_url) as http_response:  # pylint: disable=consider-using-with
    image_data = http_response.read()

  asset = resource_types.Asset(
      name=name,
      type_=enum_types.AssetTypeEnum.AssetType.IMAGE,
      image_asset=common_types.ImageAsset(data=image_data),
  )

  operation = service_types.AssetOperation(create=asset)

  try:
    response = service.mutate_assets(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  return {"resource_name": response.results[0].resource_name}


@mcp.tool()
def add_image_extension_to_campaign(
    customer_id: str,
    campaign_resource_name: str,
    asset_resource_name: str,
    login_customer_id: str | None = None,
) -> dict[str, str]:
  """Links an image asset to a campaign as an image extension.

  Call create_image_asset first to get the asset_resource_name, then
  use this tool to attach it to the campaign.

  Args:
      customer_id: Google Ads customer ID (digits only).
      campaign_resource_name: Full resource name of the campaign (e.g.,
        "customers/123/campaigns/456").
      asset_resource_name: Asset resource name from create_image_asset (e.g.,
        "customers/123/assets/789").
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with the created campaign asset resource_name.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("CampaignAssetService")

  campaign_asset = resource_types.CampaignAsset(
      campaign=campaign_resource_name,
      asset=asset_resource_name,
      field_type=enum_types.AssetFieldTypeEnum.AssetFieldType.IMAGE,
  )

  operation = service_types.CampaignAssetOperation(create=campaign_asset)

  try:
    response = service.mutate_campaign_assets(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  return {"resource_name": response.results[0].resource_name}
