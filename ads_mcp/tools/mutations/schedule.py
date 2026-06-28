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

"""Ad schedule (day parting) mutation tools for Google Ads API."""

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools._ads_api import common_types
from ads_mcp.tools._ads_api import enum_types
from ads_mcp.tools._ads_api import resource_types
from ads_mcp.tools._ads_api import service_types
from ads_mcp.tools.mutations.common import _get_client
from ads_mcp.tools.mutations.common import _handle_google_ads_error
from ads_mcp.tools.mutations.common import _resolve_enum
from google.ads.googleads.errors import GoogleAdsException


@mcp.tool()
def create_ad_schedule(
    customer_id: str,
    campaign_resource_name: str,
    schedules: list[dict],
    login_customer_id: str | None = None,
) -> dict[str, list[str]]:
  """Creates ad schedule (day parting) rules for a campaign.

  Controls which days and hours ads are shown.

  Args:
      customer_id: Google Ads customer ID (digits only).
      campaign_resource_name: Resource name of the campaign.
      schedules: List of schedule dicts, each with:
        - day_of_week: MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY,
          SATURDAY, SUNDAY
        - start_hour: 0-23 (e.g., 8 for 8:00 AM)
        - end_hour: 0-24 (e.g., 22 for 10:00 PM, 24 for midnight)
        - start_minute: ZERO, FIFTEEN, THIRTY, FORTY_FIVE (default ZERO)
        - end_minute: ZERO, FIFTEEN, THIRTY, FORTY_FIVE (default ZERO)
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with list of created criterion resource_names.

  Example:
      schedules=[
        {"day_of_week": "SUNDAY", "start_hour": 8, "end_hour": 23},
        {"day_of_week": "MONDAY", "start_hour": 8, "end_hour": 23},
      ]
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("CampaignCriterionService")

  operations = []
  for sched in schedules:
    day = _resolve_enum(
        enum_types.DayOfWeekEnum.DayOfWeek,
        sched["day_of_week"],
        "day_of_week",
    )

    start_min = _resolve_enum(
        enum_types.MinuteOfHourEnum.MinuteOfHour,
        sched.get("start_minute", "ZERO"),
        "start_minute",
    )

    end_min = _resolve_enum(
        enum_types.MinuteOfHourEnum.MinuteOfHour,
        sched.get("end_minute", "ZERO"),
        "end_minute",
    )

    ad_schedule = common_types.AdScheduleInfo(
        day_of_week=day,
        start_hour=sched["start_hour"],
        end_hour=sched["end_hour"],
        start_minute=start_min,
        end_minute=end_min,
    )

    criterion = resource_types.CampaignCriterion(
        campaign=campaign_resource_name,
        ad_schedule=ad_schedule,
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
def remove_ad_schedule(
    customer_id: str,
    campaign_id: str,
    criterion_id: str,
    login_customer_id: str | None = None,
) -> dict[str, str]:
  """Removes an ad schedule criterion from a campaign.

  Args:
      customer_id: Google Ads customer ID (digits only).
      campaign_id: Campaign ID (digits only).
      criterion_id: Criterion ID of the ad schedule to remove.
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
