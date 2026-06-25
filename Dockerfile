FROM python:3.12-slim

WORKDIR /app

# Copy project files
COPY . .

# Install the project and all dependencies
RUN pip install --no-cache-dir .

# FastMCP serves on port 8000 by default
# Set container port to 8000 in Cloud Run service settings
EXPOSE 8000

# Run the MCP server in streamable-http mode
CMD ["run-mcp-server"]
