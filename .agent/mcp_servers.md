# MCP Servers Configuration

To fully enable the **Autonomous Wealth Architect**, we use the Model Context Protocol (MCP) to give agents direct access to tools.

## Required Servers

### 1. `finance-mcp`
- **Purpose**: A wrapper around `yfinance` to allow agents to fetch data without writing Python scripts every time.
- **Tools**:
    - `get_ticker_price(ticker: str)`
    - `get_company_info(ticker: str)`
    - `get_historical_data(ticker: str, period: str)`
- **Configuration**:
    ```json
    {
      "mcpServers": {
        "finance": {
          "command": "uvx",
          "args": ["finance-mcp"]
        }
      }
    }
    ```

### 2. `filesystem-mcp` (Default)
- **Purpose**: Allows agents to read the `config.json` and portfolio CSV files.

## Future Expansions
- **`news-mcp`**: A server to fetch live news headlines for sentiment analysis (could wrap NewsAPI).
- **`llm-mcp`**: A server to offload heavy reasoning tasks to a dedicated reasoning model.

---

## 3. `agent-browser` — Headless Browser for AI Agents

- **Project**: [github.com/vercel-labs/agent-browser](https://github.com/vercel-labs/agent-browser) | [agent-browser.dev](https://agent-browser.dev)
- **Purpose**: Gives DEV AGENTS and CI workflows live "eyes" on the running Streamlit app (`http://localhost:8501`) without needing a full Playwright test suite. Uses a **Snapshot + Refs** system that returns a compact accessibility tree (~200-400 tokens) instead of a full DOM blob (~3,000-5,000 tokens), making it context-window-efficient.
- **Works with**: Gemini, Claude, OpenAI Codex, GitHub Copilot, Cursor — any agent that can run shell commands.

### Install (macOS)
```bash
brew install agent-browser
# or cross-platform:
npm install -g agent-browser
agent-browser install  # downloads Chromium (first time only)
```

### Usage by DEV AGENTS
```bash
# Start a session against the running Streamlit app
agent-browser open http://localhost:8501

# Get a compact, token-efficient snapshot of the current page
agent-browser snapshot -i
# Output example:
#   - heading "AI Stock Research Assistant" [ref=e1]
#   - combobox "Choose the app mode" [ref=e2]
#   - button "Generate Portfolio" [ref=e3]

# Interact by ref — no fragile CSS selectors needed
agent-browser click @e2
agent-browser screenshot audit.png
agent-browser close
```

### Configuration for CI
See `.github/workflows/e2e-tests.yml` — `agent-browser` is installed and run in the `AI-Driven UI Validation` step after the Streamlit server starts.
