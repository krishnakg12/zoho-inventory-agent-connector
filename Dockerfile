# Multi-stage Dockerfile for Zoho Inventory MCP Connector
FROM python:3.12-slim as builder

# Install uv for fast, reliable dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy project definition and source
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Install application and production dependencies into a virtual environment
RUN uv venv /opt/venv && \
    uv pip install --no-cache -p /opt/venv .

# -----------------------------------------------------------------------------
# Runtime stage
# -----------------------------------------------------------------------------
FROM python:3.12-slim as runtime

WORKDIR /app

# Run as non-privileged security user
RUN useradd -m -u 1000 appuser

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Copy project files
COPY --chown=appuser:appuser src/ ./src/

USER appuser

# Stdio MCP entrypoint
ENTRYPOINT ["zoho-mcp-server"]
