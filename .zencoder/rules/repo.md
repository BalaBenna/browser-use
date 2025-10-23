---
description: Repository Information Overview
alwaysApply: true
---

# Browser-Use Information

## Summary
Browser-Use is an async Python library that enables AI agents to autonomously interact with web browsers using Chrome DevTools Protocol (CDP). It allows AI models to navigate websites, fill forms, extract data, and complete complex web tasks by processing HTML and making LLM-driven decisions.

## Structure
- **browser_use/**: Main package with core components
  - **agent/**: Agent orchestration and LLM interaction
  - **browser/**: Browser session management and CDP integration
  - **dom/**: DOM processing and element highlighting
  - **llm/**: LLM provider integrations (OpenAI, Anthropic, Google, etc.)
  - **tools/**: Action registry for browser operations
- **examples/**: Usage examples for different scenarios
- **tests/**: Test suite with CI integration tests
- **web/**: Web interface components (Next.js)

## Language & Runtime
**Language**: Python
**Version**: >=3.11,<4.0
**Build System**: Hatchling
**Package Manager**: uv (recommended over pip)

## Dependencies
**Main Dependencies**:
- cdp-use>=1.4.0: CDP protocol access
- bubus>=1.5.6: Event bus for component coordination
- pydantic>=2.11.5: Data validation and settings management
- httpx>=0.28.1: HTTP client
- beautifulsoup4>=4.12.3: HTML parsing
- openai>=1.99.2: OpenAI API integration
- anthropic>=0.58.2: Anthropic API integration
- google-genai>=1.29.0: Google AI integration

**Development Dependencies**:
- ruff>=0.11.2: Linting and formatting
- pytest>=8.3.5: Testing framework
- pyright>=1.1.403: Type checking
- pytest-httpserver>=1.0.8: HTTP server for testing

## Build & Installation
```bash
# Setup with uv (recommended)
uv venv --python 3.11
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv sync

# Install browser dependencies
uvx playwright install chromium --with-deps --no-shell

# Run tests
uv run pytest -vxs tests/ci
```

## Docker
**Dockerfile**: Dockerfile, Dockerfile.fast
**Image**: python:3.12-slim base
**Configuration**: Includes Chromium browser, fonts, and all dependencies

## Testing
**Framework**: pytest with pytest-asyncio
**Test Location**: tests/ci/ directory
**Configuration**: pytest.ini_options in pyproject.toml
**Run Command**:
```bash
uv run pytest -vxs tests/ci
```

## MCP Integration
Browser-Use can run as a Model Context Protocol (MCP) server, providing browser automation tools to MCP clients like Claude Desktop. It can also connect to external MCP servers to extend agent capabilities.

## Web Component
**Framework**: Next.js
**Location**: web/ directory
**Dependencies**: Managed via npm in package.json