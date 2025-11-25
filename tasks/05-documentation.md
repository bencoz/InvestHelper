# Task 05: Documentation Improvements

## Overview
Enhance project documentation to make it more comprehensive, accessible, and maintainable.

## Priority
**Medium** - Good documentation improves onboarding and maintainability.

## Estimated Effort
3-4 hours

## Current State

### Existing Documentation
- ✅ Good README.md with overview and setup instructions
- ✅ Basic docstrings in some functions
- ❌ No API documentation
- ❌ No architecture documentation
- ❌ No contributing guidelines
- ❌ Inconsistent docstring format

## Improvements Needed

### 1. Comprehensive Code Documentation

#### Add Complete Docstrings
Use Google-style docstrings consistently:

```python
def calculate_diversification_score(portfolio_df: pd.DataFrame) -> tuple[float, pd.DataFrame]:
    """
    Calculates the diversification score of a portfolio using the Herfindahl-Hirschman Index.
    
    The diversification score measures how well-distributed a portfolio is across different
    sectors. A higher score (closer to 100) indicates better diversification, while a lower
    score suggests concentration in fewer sectors.
    
    Args:
        portfolio_df: DataFrame containing portfolio holdings with columns:
            - symbol (str): Stock ticker symbol
            - Qty (int/float): Number of shares held
            
    Returns:
        A tuple containing:
            - diversification_score (float): Score from 0-100, where higher is better
            - processed_df (pd.DataFrame): Input DataFrame enhanced with columns:
                - sector (str): Stock's business sector
                - current_price (float): Current market price
                - market_value (float): Total value of holding (Qty × current_price)
    
    Raises:
        ValueError: If portfolio_df is empty or missing required columns
        
    Example:
        >>> portfolio = pd.DataFrame({
        ...     'symbol': ['AAPL', 'MSFT', 'JPM'],
        ...     'Qty': [10, 5, 15]
        ... })
        >>> score, enhanced_df = calculate_diversification_score(portfolio)
        >>> print(f"Diversification Score: {score:.1f}/100")
        Diversification Score: 75.3/100
        
    Note:
        This function makes API calls to fetch current prices and sector information.
        Consider using cached versions for better performance.
        
    See Also:
        - suggest_rebalancing_actions(): Generate improvement suggestions
        - HHI: https://en.wikipedia.org/wiki/Herfindahl%E2%80%93Hirschman_index
    """
    # Implementation...
```

#### Documentation Standards

```python
# docstring_template.py
"""
Module for [brief description].

This module provides [detailed description of what this module does and when to use it].

Typical usage example:

    from module import function
    result = function(parameter)
    
Classes:
    ClassName: Brief description
    
Functions:
    function_name: Brief description
    
Constants:
    CONSTANT_NAME: Brief description
"""

def function_template(
    param1: str,
    param2: int,
    optional_param: float = 1.0
) -> dict:
    """
    [One-line summary - what does this function do?]
    
    [Detailed description - how does it work? When should it be used?
    Any important caveats or considerations?]
    
    Args:
        param1: [Description of param1]
        param2: [Description of param2]
        optional_param: [Description with default value]. Defaults to 1.0.
        
    Returns:
        [Description of return value, including structure if dict/list]
        
    Raises:
        ValueError: [When this error is raised]
        TypeError: [When this error is raised]
        
    Example:
        >>> result = function_template("test", 42)
        >>> print(result)
        {'key': 'value'}
        
    Note:
        [Any additional notes, warnings, or important information]
        
    See Also:
        related_function(): [Brief description of relationship]
    """
    pass
```

### 2. Architecture Documentation

Create `docs/ARCHITECTURE.md`:

```markdown
# InvestHelper Architecture

## Overview

InvestHelper is a Streamlit-based web application for stock analysis and portfolio management.
The architecture follows a modular design with clear separation of concerns.

## High-Level Architecture

```
┌─────────────────────────────────────────────────┐
│              User Interface (Streamlit)          │
│  app.py - Main application with 3 modes         │
└───────────────────┬─────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼────────┐
│  Business Logic │    │  Utility Modules │
│                 │    │                  │
│ stock_utils.py  │    │  io_utils.py     │
│ main.py         │    │  constants.py    │
│ research_stock  │    │  cache.py        │
└───────┬─────────┘    └────────┬─────────┘
        │                       │
        └───────────┬───────────┘
                    │
        ┌───────────▼────────────┐
        │   External Services     │
        │                         │
        │  yfinance API          │
        │  (Yahoo Finance)       │
        └─────────────────────────┘
```

## Module Breakdown

### Presentation Layer
- **app.py**: Streamlit UI, handles user interaction, displays visualizations

### Business Logic Layer
- **stock_utils.py**: Core stock analysis algorithms
  - Technical indicators (MA, RSI, MACD, etc.)
  - Backtesting engine
  - Portfolio generation
  - Diversification scoring
  
- **main.py**: CLI interface (legacy)
- **research_stock.py**: Stock research tools (legacy)

### Utility Layer
- **io_utils.py**: Input/output operations, plotting functions
- **constants.py**: Application constants and configuration
- **cache.py**: Data caching mechanisms
- **logging_config.py**: Logging setup

### Data Layer
- **yfinance**: External API for stock market data
- **Cache**: Local data persistence (.cache directory)

## Data Flow

### Portfolio Generation Flow
```
User Input (amount, preferences)
    ↓
prepare_stock_selection() → Filter stocks by type
    ↓
fetch_stock_data() → Get historical prices from yfinance
    ↓
generate_portfolio() → Allocate budget across stocks
    ↓
Display results in Streamlit
```

### Stock Analysis Flow
```
User Input (ticker, date range)
    ↓
get_stock_data() → Fetch from yfinance (or cache)
    ↓
ma_strategy() → Calculate moving averages & signals
    ↓
buy_sell_signals() → Identify trade points
    ↓
backtest() → Simulate trading strategy
    ↓
RSI() → Calculate momentum indicator
    ↓
Visualize results (matplotlib charts)
```

### Portfolio Analysis Flow
```
Upload CSV file
    ↓
Validate columns (symbol, Qty)
    ↓
Parallel fetch: get_stock_sector_cached() + get_current_price_cached()
    ↓
Calculate market values
    ↓
Compute HHI diversification score
    ↓
Display score & sector allocation pie chart
    ↓
(Optional) suggest_rebalancing_actions()
```

## Key Design Patterns

### 1. Caching Strategy
- **L1 Cache**: In-memory (15 min TTL) for frequently accessed data
- **L2 Cache**: Disk-based (24 hour TTL) for persistence
- **Cache Key Format**: `{operation}:{ticker}:{params}`

### 2. Error Handling
- Custom exception hierarchy
- Retry with exponential backoff for API calls
- Graceful degradation (return "Unknown" for missing sector data)

### 3. Parallel Processing
- ThreadPoolExecutor for concurrent API calls
- Configurable worker pool size
- Maintains result ordering

## Configuration

### config.json
```json
{
  "dividend_stocks": [...],
  "growth_stocks": [...],
  "index_funds": [...]
}
```

### Environment Variables
- `LOG_LEVEL`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `CACHE_DIR`: Cache directory location
- `MAX_WORKERS`: Parallel processing thread count

## Testing Strategy

### Unit Tests (tests/)
- `test_stock_utils.py`: Business logic validation
- `test_io_utils.py`: I/O operations

### E2E Tests (tests/e2e/)
- Playwright-based UI testing
- Simulates user workflows
- Validates end-to-end functionality

## Deployment

Currently runs locally via:
```bash
streamlit run app.py
```

Future: Docker containerization for easier deployment

## Performance Considerations

1. **API Rate Limiting**: yfinance has implicit rate limits
2. **Cache Hit Rate**: Target >80% for repeat queries
3. **Parallel Processing**: 5-10 workers optimal for portfolio analysis
4. **Memory**: Cache size should stay <100MB

## Security

- No authentication required (local use)
- No sensitive data stored
- API keys not required for yfinance
- CSV uploads validated for structure

## Future Enhancements

- WebSocket for real-time price updates
- Database for historical query storage
- User accounts & saved portfolios
- Mobile-responsive UI
```

### 3. Contributing Guidelines

Create `docs/CONTRIBUTING.md`:

```markdown
# Contributing to InvestHelper

Thank you for considering contributing to InvestHelper! This document provides
guidelines and instructions for contributing.

## Development Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd InvestHelper
```

2. Create virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Run tests to verify setup:
```bash
pytest tests/
```

## Code Style

### Python Style Guide
- Follow PEP 8
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use meaningful variable names

### Docstrings
- Use Google-style docstrings
- Include examples for public functions
- Document all parameters and return values

### Example:
```python
def calculate_score(value: float, threshold: float = 0.5) -> bool:
    """
    Determines if value exceeds threshold.
    
    Args:
        value: The value to check
        threshold: Minimum value to pass. Defaults to 0.5.
        
    Returns:
        True if value >= threshold, False otherwise
        
    Example:
        >>> calculate_score(0.7)
        True
    """
    return value >= threshold
```

## Testing

### Running Tests
```bash
# All tests
pytest

# Unit tests only
pytest tests/ -k "not e2e"

# E2E tests only
pytest tests/e2e/

# With coverage
pytest --cov=. --cov-report=html
```

### Writing Tests
- Write tests for all new functionality
- Aim for >80% code coverage
- Use fixtures for common setup
- Mock external API calls

## Pull Request Process

1. **Fork the repository**

2. **Create a feature branch:**
```bash
git checkout -b feature/your-feature-name
```

3. **Make your changes:**
   - Write code
   - Add tests
   - Update documentation

4. **Run linting and tests:**
```bash
# Format code
black .

# Run linter
pylint *.py

# Run tests
pytest
```

5. **Commit your changes:**
```bash
git add .
git commit -m "feat: add X feature"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding tests
- `refactor:` Code refactoring
- `perf:` Performance improvements

6. **Push to your fork:**
```bash
git push origin feature/your-feature-name
```

7. **Open a Pull Request**

### PR Checklist
- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] No breaking changes (or documented if necessary)
- [ ] Commits follow conventional commit format

## Project Structure

```
InvestHelper/
├── app.py                 # Main Streamlit application
├── stock_utils.py         # Core analysis functions
├── main.py                # CLI interface
├── io_utils.py            # I/O utilities
├── constants.py           # Configuration constants
├── config.json            # Stock lists configuration
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
├── tests/                 # Test suite
│   ├── test_stock_utils.py
│   └── e2e/              # End-to-end tests
├── tasks/                 # Task specifications
└── docs/                  # Documentation
    ├── ARCHITECTURE.md
    └── CONTRIBUTING.md
```

## Adding New Features

### Checklist
1. Check if similar feature exists
2. Open an issue to discuss (for large features)
3. Create specification in `tasks/` directory
4. Implement with tests
5. Update documentation
6. Submit PR

### Feature Template
```python
# my_feature.py
"""
Module for [feature name].

This module provides [what it does].
"""

from typing import ...

def my_feature_function(...) -> ...:
    """
    [Description]
    
    Args:
        ...
    
    Returns:
        ...
        
    Example:
        >>> ...
    """
    pass
```

## Reporting Bugs

### Bug Report Template
```markdown
**Description**
Clear description of the bug

**To Reproduce**
Steps to reproduce:
1. Go to '...'
2. Click on '....'
3. See error

**Expected Behavior**
What should happen

**Actual Behavior**
What actually happens

**Environment**
- OS: [e.g., macOS 12.0]
- Python Version: [e.g., 3.9.7]
- InvestHelper Version: [e.g., commit hash]

**Screenshots**
If applicable

**Additional Context**
Any other relevant information
```

## Code Review Guidelines

### For Reviewers
- Be constructive and respectful
- Focus on code quality, not personal preferences
- Explain reasoning for requested changes
- Approve when satisfied, or request changes with clear guidance

### For Contributors
- Respond to feedback promptly
- Don't take criticism personally
- Ask questions if feedback is unclear
- Make requested changes or discuss alternatives

## Community

- Be respectful and inclusive
- Help others when possible
- Provide constructive feedback
- Follow the code of conduct

## Questions?

If you have questions, please:
1. Check existing documentation
2. Search closed issues
3. Open a new issue with the "question" label

Thank you for contributing! 🚀
```

### 4. User Guide

Create `docs/USER_GUIDE.md`:

```markdown
# InvestHelper User Guide

Complete guide to using the InvestHelper stock analysis tool.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Portfolio Generator](#portfolio-generator)
3. [Stock Analyzer](#stock-analyzer)
4. [Portfolio Analyzer](#portfolio-analyzer)
5. [Exporting Data](#exporting-data)
6. [Tips & Best Practices](#tips--best-practices)
7. [Troubleshooting](#troubleshooting)

## Getting Started

[Detailed user instructions with screenshots]

## FAQ

**Q: How often is stock data updated?**
A: Data is cached for 15 minutes. Click "Clear Cache" to force refresh.

**Q: What date range should I use for analysis?**
A: For moving average strategies, use at least 1 year of data...

[More FAQs]
```

### 5. API Documentation

Generate with Sphinx:

```bash
# Install Sphinx
pip install sphinx sphinx-rtd-theme

# Initialize
cd docs/
sphinx-quickstart

# Configure conf.py
# Build
make html
```

## Implementation Steps

### Phase 1: Code Documentation (2 hours)
- [ ] Add comprehensive docstrings to all functions in `stock_utils.py`
- [ ] Add comprehensive docstrings to all functions in `main.py`
- [ ] Add comprehensive docstrings to `app.py`
- [ ] Standardize docstring format (Google style)
- [ ] Add module-level documentation

### Phase 2: Architecture & Contributing Docs (1 hour)
- [ ] Create `docs/` directory
- [ ] Write `docs/ARCHITECTURE.md`
- [ ] Write `docs/CONTRIBUTING.md`
- [ ] Add architecture diagrams (optional, use mermaid)

### Phase 3: User Guide (1 hour)
- [ ] Write `docs/USER_GUIDE.md`
- [ ] Add screenshots of each feature
- [ ] Write FAQ section
- [ ] Add troubleshooting guide

### Phase 4: API Documentation (optional, 1 hour)
- [ ] Set up Sphinx
- [ ] Configure auto-documentation
- [ ] Build HTML docs
- [ ] Host on GitHub Pages (optional)

## File Structure

```
/Users/bencohen/Projects/python/InvestHelper/
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CONTRIBUTING.md
│   ├── USER_GUIDE.md
│   ├── screenshots/
│   │   ├── portfolio-generator.png
│   │   ├── stock-analyzer.png
│   │   └── portfolio-analyzer.png
│   └── api/  (Sphinx-generated)
├── README.md  (update with links to docs/)
└── ...
```

## Tools

- **Docstring Validation**: `pydocstyle`
- **Documentation Generation**: `sphinx`, `pdoc`
- **Diagram Creation**: `mermaid`, `draw.io`
- **Screenshot Tools**: macOS Screenshot, Snagit

## Success Criteria

- ✅ All public functions have complete docstrings
- ✅ Architecture is clearly documented
- ✅ Contributing guidelines are clear
- ✅ User guide covers all features
- ✅ New contributors can onboard easily
- ✅ README links to all documentation

## Related Tasks

- Task 01 (Code Quality) - Clean code is easier to document
- Task 04 (New Features) - Document new features as added

## Notes

- Keep documentation in sync with code
- Use version control for docs
- Consider documentation as code
- Review docs during PR process
- Add doc checks to CI/CD pipeline (future)
