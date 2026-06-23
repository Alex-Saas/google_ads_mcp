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

"""Budget mutation tools for Google Ads API."""

from ads_mcp.coordinator import mcp_server as mcp
from ads_mcp.tools._ads_api import enum_types
from ads_mcp.tools._ads_api import resource_types
from ads_mcp.tools._ads_api import service_types
from ads_mcp.tools.mutations.common import _get_client
from ads_mcp.tools.mutations.common import _handle_google_ads_error
from ads_mcp.tools.mutations.common import _resolve_enum
from google.ads.googleads.errors import GoogleAdsException
from google.protobuf import field_mask_pb2


@mcp.tool()
def create_campaign_budget(
    customer_id: str,
    name: str,
    amount_micros: int,
    delivery_method: str = "STANDARD",
    login_customer_id: str | None = None,
) -> dict[str, str]:
  """Creates a campaign budget.

  Args:
      customer_id: Google Ads customer ID (digits only).
      name: Name for the budget (e.g., "GoIELTS Daily Budget").
      amount_micros: Daily budget in micros (e.g., 4000000 = $4.00).
      delivery_method: STANDARD or ACCELERATED. Default STANDARD.
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with the budget resource_name.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("CampaignBudgetService")

  budget = resource_types.CampaignBudget(
      name=name,
      amount_micros=amount_micros,
      delivery_method=_resolve_enum(
          enum_types.BudgetDeliveryMethodEnum.BudgetDeliveryMethod,
          delivery_method,
          "delivery_method",
      ),
  )

  operation = service_types.CampaignBudgetOperation(create=budget)
  try:
    response = service.mutate_campaign_budgets(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  resource_name = response.results[0].resource_name
  return {"resource_name": resource_name}


@mcp.tool()
def update_campaign_budget_amount(
    customer_id: str,
    budget_resource_name: str,
    amount_micros: int,
    login_customer_id: str | None = None,
) -> dict[str, str]:
  """Updates an existing campaign budget amount.

  Args:
      customer_id: Google Ads customer ID (digits only).
      budget_resource_name: Full resource name of the budget
        (e.g., "customers/123/campaignBudgets/456").
      amount_micros: New daily budget in micros (e.g., 5000000 = $5.00,
        equivalent to approximately 18.75 SAR at current rates).
      login_customer_id: MCC account ID if customer is managed.

  Returns:
      Dict with the updated budget resource_name.
  """
  ads_client = _get_client(login_customer_id)
  service = ads_client.get_service("CampaignBudgetService")

  budget = resource_types.CampaignBudget(
      resource_name=budget_resource_name,
      amount_micros=amount_micros,
  )

  operation = service_types.CampaignBudgetOperation(update=budget)
  operation.update_mask.CopyFrom(
      field_mask_pb2.FieldMask(paths=["amount_micros"])
  )

  try:
    response = service.mutate_campaign_budgets(
        customer_id=customer_id, operations=[operation]
    )
  except GoogleAdsException as e:
    _handle_google_ads_error(e)

  return {"resource_name": response.results[0].resource_name}
