# Task 04: New Features

## Overview
Add new functionality to enhance the user experience and provide more comprehensive stock analysis capabilities.

## Priority
**Medium** - Nice-to-have features that add significant value.

## Estimated Effort
8-10 hours total (can be split into sub-tasks)

## Feature 1: Export Functionality

### Requirements
Allow users to export:
- Generated portfolios (CSV, Excel)
- Stock analysis results (PDF report, CSV data)
- Charts (PNG, SVG)
- Portfolio diversification analysis (PDF report)

### Implementation

```python
# export_utils.py
import pandas as pd
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
from typing import Optional, Dict, Any
import io

class DataExporter:
    """Handles exporting data in various formats."""
    
    def __init__(self, export_dir: str = "exports"):
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(exist_ok=True)
    
    def export_portfolio_csv(
        self,
        portfolio_df: pd.DataFrame,
        filename: Optional[str] = None
    ) -> Path:
        """Export portfolio to CSV."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"portfolio_{timestamp}.csv"
        
        filepath = self.export_dir / filename
        portfolio_df.to_csv(filepath, index=False)
        logger.info(f"Portfolio exported to {filepath}")
        return filepath
    
    def export_portfolio_excel(
        self,
        portfolio_df: pd.DataFrame,
        metadata: Optional[Dict[str, Any]] = None,
        filename: Optional[str] = None
    ) -> Path:
        """Export portfolio to Excel with formatting."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"portfolio_{timestamp}.xlsx"
        
        filepath = self.export_dir / filename
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Portfolio sheet
            portfolio_df.to_excel(writer, sheet_name='Portfolio', index=False)
            
            # Metadata sheet
            if metadata:
                meta_df = pd.DataFrame([metadata])
                meta_df.to_excel(writer, sheet_name='Info', index=False)
        
        logger.info(f"Portfolio exported to {filepath}")
        return filepath
    
    def export_analysis_report_pdf(
        self,
        ticker: str,
        analysis_data: Dict[str, Any],
        figures: list,
        filename: Optional[str] = None
    ) -> Path:
        """
        Export comprehensive stock analysis report as PDF.
        
        Requires: pip install reportlab matplotlib
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{ticker}_{timestamp}.pdf"
        
        filepath = self.export_dir / filename
        doc = SimpleDocTemplate(str(filepath), pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        story.append(Paragraph(f"Stock Analysis Report: {ticker}", styles['Title']))
        story.append(Spacer(1, 0.2*inch))
        
        # Analysis metadata
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
        story.append(Paragraph(f"Period: {analysis_data.get('start_date')} to {analysis_data.get('end_date')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Key metrics table
        metrics_data = [
            ['Metric', 'Value'],
            ['MA Strategy Final Wealth', f"${analysis_data.get('ma_final_wealth', 0):,.2f}"],
            ['Buy & Hold Final Wealth', f"${analysis_data.get('bh_final_wealth', 0):,.2f}"],
            ['MA Strategy Return', f"{analysis_data.get('ma_return', 0):.2f}%"],
            ['Buy & Hold Return', f"{analysis_data.get('bh_return', 0):.2f}%"],
        ]
        
        table = Table(metrics_data)
        story.append(table)
        story.append(Spacer(1, 0.3*inch))
        
        # Add charts
        for fig in figures:
            # Save figure to bytes
            img_buffer = io.BytesIO()
            fig.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
            img_buffer.seek(0)
            
            # Add to PDF
            img = Image(img_buffer, width=6*inch, height=3.5*inch)
            story.append(img)
            story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(story)
        logger.info(f"Analysis report exported to {filepath}")
        return filepath
    
    def export_chart_png(
        self,
        figure: plt.Figure,
        filename: Optional[str] = None,
        dpi: int = 300
    ) -> Path:
        """Export matplotlib figure as high-res PNG."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"chart_{timestamp}.png"
        
        filepath = self.export_dir / filename
        figure.savefig(filepath, dpi=dpi, bbox_inches='tight', format='png')
        logger.info(f"Chart exported to {filepath}")
        return filepath

# Integration in app.py
exporter = DataExporter()

if st.button("Export Portfolio as CSV"):
    filepath = exporter.export_portfolio_csv(portfolio_df)
    with open(filepath, 'rb') as f:
        st.download_button(
            label="Download CSV",
            data=f,
            file_name=filepath.name,
            mime='text/csv'
        )

if st.button("Export Analysis Report as PDF"):
    report_data = {
        'ticker': stock_ticker,
        'start_date': start_date_input.strftime('%Y-%m-%d'),
        'end_date': datetime.today().strftime('%Y-%m-%d'),
        'ma_final_wealth': final_ma_wealth,
        'bh_final_wealth': final_lt_wealth,
        'ma_return': ((final_ma_wealth - initial_wealth) / initial_wealth * 100),
        'bh_return': ((final_lt_wealth - initial_wealth) / initial_wealth * 100),
    }
    
    figures = [fig_price_ma, fig_wealth, fig_rsi]
    filepath = exporter.export_analysis_report_pdf(
        stock_ticker,
        report_data,
        figures
    )
    
    with open(filepath, 'rb') as f:
        st.download_button(
            label="Download PDF Report",
            data=f,
            file_name=filepath.name,
            mime='application/pdf'
        )
```

## Feature 2: Stock Comparison

### Requirements
Allow users to compare multiple stocks side-by-side:
- Price trends
- Performance metrics
- Risk metrics
- Correlation analysis

### Implementation

```python
# comparison_utils.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from typing import List, Dict
import yfinance as yf

def compare_stocks(
    tickers: List[str],
    start_date: str,
    end_date: str
) -> Dict[str, pd.DataFrame]:
    """
    Compare multiple stocks across various metrics.
    
    Returns:
        Dictionary with comparison data and metrics
    """
    # Fetch data for all tickers
    data = {}
    for ticker in tickers:
        df = get_stock_data_cached(ticker, start_date, end_date, None, '1d')
        if not df.empty:
            data[ticker] = df
    
    if not data:
        raise ValueError("No data available for any of the provided tickers")
    
    # Calculate normalized prices (all start at 100)
    normalized = pd.DataFrame()
    for ticker, df in data.items():
        normalized[ticker] = (df['Close'] / df['Close'].iloc[0]) * 100
    
    # Calculate returns
    returns = pd.DataFrame()
    for ticker, df in data.items():
        returns[ticker] = df['Close'].pct_change()
    
    # Calculate metrics
    metrics = []
    for ticker in tickers:
        if ticker not in data:
            continue
            
        df = data[ticker]
        ticker_returns = returns[ticker].dropna()
        
        metrics.append({
            'Ticker': ticker,
            'Total Return %': ((df['Close'].iloc[-1] / df['Close'].iloc[0]) - 1) * 100,
            'Volatility (Ann.)': ticker_returns.std() * np.sqrt(252) * 100,
            'Sharpe Ratio': (ticker_returns.mean() / ticker_returns.std()) * np.sqrt(252) if ticker_returns.std() != 0 else 0,
            'Max Drawdown %': calculate_max_drawdown(df['Close']),
            'Current Price': df['Close'].iloc[-1],
            '52W High': df['Close'].max(),
            '52W Low': df['Close'].min(),
        })
    
    metrics_df = pd.DataFrame(metrics)
    
    # Calculate correlation matrix
    correlation = returns.corr()
    
    return {
        'price_data': data,
        'normalized_prices': normalized,
        'returns': returns,
        'metrics': metrics_df,
        'correlation': correlation
    }

def calculate_max_drawdown(prices: pd.Series) -> float:
    """Calculate maximum drawdown percentage."""
    cummax = prices.cummax()
    drawdown = (prices - cummax) / cummax * 100
    return drawdown.min()

def plot_stock_comparison(comparison_data: Dict) -> plt.Figure:
    """Create comparison visualization."""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    
    # Normalized price comparison
    ax1 = axes[0, 0]
    comparison_data['normalized_prices'].plot(ax=ax1, linewidth=2)
    ax1.set_title('Normalized Price Comparison (Base = 100)')
    ax1.set_ylabel('Normalized Price')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # Correlation heatmap
    ax2 = axes[0, 1]
    corr = comparison_data['correlation']
    im = ax2.imshow(corr, cmap='RdYlGn', vmin=-1, vmax=1, aspect='auto')
    ax2.set_xticks(range(len(corr.columns)))
    ax2.set_yticks(range(len(corr.columns)))
    ax2.set_xticklabels(corr.columns, rotation=45)
    ax2.set_yticklabels(corr.columns)
    ax2.set_title('Return Correlation Matrix')
    
    # Add correlation values
    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            text = ax2.text(j, i, f'{corr.iloc[i, j]:.2f}',
                           ha="center", va="center", color="black", fontsize=10)
    
    plt.colorbar(im, ax=ax2)
    
    # Risk-Return scatter
    ax3 = axes[1, 0]
    metrics = comparison_data['metrics']
    ax3.scatter(metrics['Volatility (Ann.)'], metrics['Total Return %'], s=100)
    for idx, row in metrics.iterrows():
        ax3.annotate(row['Ticker'], 
                    (row['Volatility (Ann.)'], row['Total Return %']),
                    xytext=(5, 5), textcoords='offset points')
    ax3.set_xlabel('Annualized Volatility (%)')
    ax3.set_ylabel('Total Return (%)')
    ax3.set_title('Risk-Return Profile')
    ax3.grid(True, alpha=0.3)
    
    # Metrics table (as text)
    ax4 = axes[1, 1]
    ax4.axis('tight')
    ax4.axis('off')
    
    # Create table data
    table_data = metrics[['Ticker', 'Total Return %', 'Sharpe Ratio', 'Max Drawdown %']].round(2)
    table = ax4.table(cellText=table_data.values,
                     colLabels=table_data.columns,
                     cellLoc='center',
                     loc='center')
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 2)
    ax4.set_title('Performance Metrics', pad=20)
    
    plt.tight_layout()
    return fig

# In app.py - New comparison mode
elif app_mode == "Stock Comparison":
    st.header("Compare Multiple Stocks")
    
    # Allow users to input multiple tickers
    tickers_input = st.text_input(
        "Enter stock tickers separated by commas:",
        "AAPL,MSFT,GOOGL"
    )
    tickers = [t.strip().upper() for t in tickers_input.split(',') if t.strip()]
    
    start_date = st.date_input("Start Date", date(2020, 1, 1))
    
    if st.button("Compare Stocks") and len(tickers) >= 2:
        with st.spinner("Comparing stocks..."):
            try:
                comparison = compare_stocks(
                    tickers,
                    start_date.strftime('%Y-%m-%d'),
                    datetime.today().strftime('%Y-%m-%d')
                )
                
                st.subheader("Performance Metrics")
                st.dataframe(comparison['metrics'])
                
                st.subheader("Visual Comparison")
                fig = plot_stock_comparison(comparison)
                st.pyplot(fig)
                
                # Export option
                if st.button("Export Comparison Report"):
                    # Export logic here
                    pass
                    
            except Exception as e:
                st.error(f"Error comparing stocks: {e}")
    elif len(tickers) < 2:
        st.warning("Please enter at least 2 stock tickers to compare")
```

## Feature 3: Additional Technical Indicators

### Requirements
Add more technical analysis indicators:
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Stochastic Oscillator
- Average True Range (ATR)

### Implementation

```python
# technical_indicators.py
import pandas as pd
import numpy as np

def calculate_macd(
    df: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> pd.DataFrame:
    """
    Calculate MACD indicator.
    
    Returns DataFrame with MACD, Signal, and Histogram columns.
    """
    df = df.copy()
    
    # Calculate EMAs
    ema_fast = df['Close'].ewm(span=fast_period, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow_period, adjust=False).mean()
    
    # MACD Line
    df['MACD'] = ema_fast - ema_slow
    
    # Signal Line
    df['MACD_Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
    
    # Histogram
    df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
    
    return df

def calculate_bollinger_bands(
    df: pd.DataFrame,
    period: int = 20,
    std_dev: float = 2.0
) -> pd.DataFrame:
    """Calculate Bollinger Bands."""
    df = df.copy()
    
    # Middle band (SMA)
    df['BB_Middle'] = df['Close'].rolling(window=period).mean()
    
    # Standard deviation
    rolling_std = df['Close'].rolling(window=period).std()
    
    # Upper and Lower bands
    df['BB_Upper'] = df['BB_Middle'] + (rolling_std * std_dev)
    df['BB_Lower'] = df['BB_Middle'] - (rolling_std * std_dev)
    
    # Band width
    df['BB_Width'] = df['BB_Upper'] - df['BB_Lower']
    
    # %B indicator (position within bands)
    df['BB_PercentB'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
    
    return df

def calculate_stochastic(
    df: pd.DataFrame,
    k_period: int = 14,
    d_period: int = 3
) -> pd.DataFrame:
    """Calculate Stochastic Oscillator."""
    df = df.copy()
    
    # %K line
    low_min = df['Low'].rolling(window=k_period).min()
    high_max = df['High'].rolling(window=k_period).max()
    
    df['Stoch_K'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    
    # %D line (smoothed %K)
    df['Stoch_D'] = df['Stoch_K'].rolling(window=d_period).mean()
    
    return df

def calculate_atr(
    df: pd.DataFrame,
    period: int = 14
) -> pd.DataFrame:
    """Calculate Average True Range."""
    df = df.copy()
    
    # True Range
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    
    # ATR (smoothed TR)
    df['ATR'] = df['TR'].rolling(window=period).mean()
    
    # Cleanup
    df.drop(['H-L', 'H-PC', 'L-PC', 'TR'], axis=1, inplace=True)
    
    return df

# Visualization functions
def plot_macd(df: pd.DataFrame) -> plt.Figure:
    """Plot MACD indicator."""
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
    
    # Price
    ax1.plot(df['Date'], df['Close'], label='Close Price', linewidth=2)
    ax1.set_ylabel('Price ($)')
    ax1.set_title('Price and MACD Indicator')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # MACD
    ax2.plot(df['Date'], df['MACD'], label='MACD', linewidth=2, color='blue')
    ax2.plot(df['Date'], df['MACD_Signal'], label='Signal', linewidth=2, color='red')
    ax2.bar(df['Date'], df['MACD_Hist'], label='Histogram', alpha=0.3, color='gray')
    ax2.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax2.set_ylabel('MACD')
    ax2.set_xlabel('Date')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

def plot_bollinger_bands(df: pd.DataFrame) -> plt.Figure:
    """Plot Bollinger Bands."""
    fig, ax = plt.subplots(figsize=(14, 7))
    
    ax.plot(df['Date'], df['Close'], label='Close Price', linewidth=2, color='black')
    ax.plot(df['Date'], df['BB_Upper'], label='Upper Band', linestyle='--', color='red')
    ax.plot(df['Date'], df['BB_Middle'], label='Middle Band (SMA)', linestyle='--', color='blue')
    ax.plot(df['Date'], df['BB_Lower'], label='Lower Band', linestyle='--', color='red')
    ax.fill_between(df['Date'], df['BB_Lower'], df['BB_Upper'], alpha=0.1, color='gray')
    
    ax.set_title('Bollinger Bands')
    ax.set_ylabel('Price ($)')
    ax.set_xlabel('Date')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig

# Integration in app.py
# Add checkbox to enable advanced indicators
if st.checkbox("Show Advanced Technical Indicators"):
    # Calculate indicators
    df_with_indicators = calculate_macd(backtest_results_df.copy())
    df_with_indicators = calculate_bollinger_bands(df_with_indicators)
    
    # Display
    st.subheader("MACD Indicator")
    fig_macd = plot_macd(df_with_indicators)
    st.pyplot(fig_macd)
    
    st.subheader("Bollinger Bands")
    fig_bb = plot_bollinger_bands(df_with_indicators)
    st.pyplot(fig_bb)
```

## Implementation Steps

### Phase 1: Export Functionality (3 hours)
- [ ] Create `export_utils.py` with DataExporter class
- [ ] Implement CSV export
- [ ] Implement Excel export (requires openpyxl)
- [ ] Implement PDF export (requires reportlab)
- [ ] Implement chart export
- [ ] Add export buttons to all app modes
- [ ] Test with various data

### Phase 2: Stock Comparison (3 hours)
- [ ] Create `comparison_utils.py`
- [ ] Implement `compare_stocks()` function
- [ ] Implement comparison visualizations
- [ ] Add "Stock Comparison" mode to app
- [ ] Add export for comparison reports
- [ ] Test with multiple stocks

### Phase 3: Advanced Technical Indicators (3 hours)
- [ ] Create `technical_indicators.py`
- [ ] Implement MACD
- [ ] Implement Bollinger Bands
- [ ] Implement Stochastic Oscillator
- [ ] Implement ATR
- [ ] Create visualization functions
- [ ] Add to Stock Analyzer mode
- [ ] Add indicator selection UI

### Phase 4: Testing & Documentation (1 hour)
- [ ] Write tests for all new features
- [ ] Update README.md
- [ ] Add user guide for new features
- [ ] Create example outputs

## Dependencies

```txt
openpyxl>=3.0.0          # Excel export
reportlab>=3.6.0         # PDF export
Pillow>=9.0.0            # Image handling
scipy>=1.7.0             # Statistical calculations
```

## Success Criteria

- ✅ Users can export all data types
- ✅ Stock comparison works for 2-10 stocks
- ✅ All technical indicators calculate correctly
- ✅ Visualizations are clear and informative
- ✅ Export formats are professional quality
- ✅ All features documented

## Related Tasks

- Task 03 (Caching) - exports should use cached data
- Task 05 (Documentation) - document new features

## Notes

- Export folder should be added to `.gitignore`
- Consider file size limits for exports
- Add option to customize export format/styling
- Consider adding more indicators if users request them
