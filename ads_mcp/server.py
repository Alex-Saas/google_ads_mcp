"""The server for the Google Ads API MCP."""

import asyncio
import os

from ads_mcp.coordinator import mcp_server
from ads_mcp.scripts.generate_views import update_views_yaml
from ads_mcp.tools import accounts, docs, keyword_planner, reporting
from ads_mcp.tools._utils import get_ads_client
import dotenv
from fastmcp.server.auth.providers.google import GoogleProvider, GoogleTokenVerifier

dotenv.load_dotenv()

tools = [reporting, accounts, docs, keyword_planner]

if os.getenv("ADS_MCP_ENABLE_MUTATIONS", "false").lower() == "true":
  from ads_mcp.tools import mutations
  tools.extend([
      mutations.budget, mutations.campaign, mutations.ad_group,
      mutations.ad, mutations.criterion, mutations.sitelink,
      mutations.callout, mutations.snippet, mutations.schedule,
      mutations.audience, mutations.demographic, mutations.labels,
      mutations.shared_lists, mutations.promotion, mutations.conversion,
      mutations.experiment,
  ])

if os.getenv("USE_GOOGLE_OAUTH_ACCESS_TOKEN"):
  mcp_server.auth = GoogleTokenVerifier()

if os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID") and os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET"):
  base_url = os.getenv("FASTMCP_SERVER_BASE_URL", "http://localhost:8000")
  # NOTE: fastmcp >= 3.x requires client_secret to be passed explicitly;
  # relying on env auto-discovery raises at startup:
  #   ValueError: jwt_signing_key is required when upstream_client_secret
  #   is not provided.
  mcp_server.auth = GoogleProvider(
      client_id=os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID"),
      client_secret=os.getenv("FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET"),
      base_url=base_url,
      required_scopes=["https://www.googleapis.com/auth/adwords"],
  )


def main():
  asyncio.run(update_views_yaml())
  get_ads_client()
  port = int(os.environ.get("PORT", 8000))
  print(f"mcp server starting on port {port}...")
  mcp_server.run(transport="streamable-http", host="0.0.0.0", port=port, show_banner=False)


if __name__ == "__main__":
  main()
