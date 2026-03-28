# Task 09: Agent Skills Standardization (agentskills.io)

## Overview
Migrate the existing `.agent/skills/*.md` files into modular, executable agent skills conforming to the `agentskills.io` standard. Additionally, build a new `sentiment_analyst` skill to retrieve alternative data. This is Phase 1 of the Agentic Pivot roadmap.

## Priority
**High (Agentic Architecture Block)** - Required before the Conversational UI (Phase 2) can be built.

## Estimated Effort
3-4 hours

## Current Issues
1. `.agent/skills/data_acquisition.md`, `portfolio_management.md`, and `technical_analysis.md` are flat markdown files. 
2. They do not have dedicated execution scripts associated with them in an encapsulated folder structure, breaking the `agentskills.io` standard.
3. The platform lacks alternative data ingestion for a competitive edge.

## Implementation Steps

### 1. Structure the `data_scout` Skill (1 hour)
- [ ] Create directory: `.agent/skills/data_scout/`
- [ ] Move instructions from `data_acquisition.md` into `.agent/skills/data_scout/SKILL.md` and format with YAML frontmatter (`name: Data Scout`, `description: Fetches raw market data`).
- [ ] Create `.agent/skills/data_scout/scripts/fetch_financials.py`. Copy the core raw fetching logic from `stock_utils.py` (`get_stock_data`) into this script, formatting the output strictly as JSON or Markdown explicitly so an LLM can pipe the output.

### 2. Structure the `technical_analyst` Skill (1 hour)
- [ ] Create directory: `.agent/skills/technical_analyst/`
- [ ] Move `technical_analysis.md` into `SKILL.md` (Add YAML frontmatter).
- [ ] Create `scripts/run_indicators.py` acting as an entry point for RSI/MA calculations.

### 3. Structure the `portfolio_manager` Skill (30 mins)
- [ ] Create directory: `.agent/skills/portfolio_manager/`
- [ ] Move `portfolio_management.md` into `SKILL.md` (Add YAML frontmatter).
- [ ] Create `scripts/score_diversity.py` wrapping the `calculate_diversification_score` function.

### 4. Build the NEW `sentiment_analyst` Skill (1-2 hours)
- [ ] Create directory: `.agent/skills/sentiment_analyst/`
- [ ] Create `SKILL.md` documenting how the agent should interpret title sentiment.
- [ ] Create `scripts/scrape_news.py`.
    - **Implementation Note**: Use `yfinance` news property (`yf.Ticker(symbol).news`) or a free service like DuckDuckGo search API to pull the last 5 headlines for the ticker. 
    - Output a format like: `Headline: [Title], Publisher: [Org]`.

### 5. Cleanup
- [ ] Delete the old flat `.agent/skills/*.md` files to prevent conflicting instructions.

## Success Criteria
- ✅ Four explicit directories exist in `.agent/skills/` (`data_scout`, `technical_analyst`, `portfolio_manager`, `sentiment_analyst`).
- ✅ Every directory contains a valid `SKILL.md` with YAML frontmatter.
- ✅ Every directory has a `scripts/` folder with at least one executable python script.
- ✅ Running `python .agent/skills/sentiment_analyst/scripts/scrape_news.py AAPL` outputs raw news headlines in stdout.

## Dependencies
This task does not depend on past UI tasks. The scripts should leverage the foundational functions inside `stock_utils.py`/`main.py` but expose them as CLI tools for LLMs.
