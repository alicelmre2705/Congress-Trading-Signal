# Congressional Trading Strategy Project - Final Status Report

## 📋 Project Overview

This project implements a quantitative trading strategy that follows US Congress members' stock trading disclosures. The strategy mimics congressional trades (buy when they buy, sell when they sell) using data from the House of Representatives Financial Disclosure website.

**Current Status**: ✅ **Data Collection Complete** | ⚠️ **Data Quality Issues Present** | 🔄 **Ready for Enhanced Processing**

---

## 🎯 Project Objectives

1. **Primary Goal**: Create a congressional trading following strategy similar to Quiver Quant's "Congress Buys"
2. **Data Source**: https://disclosures-clerk.house.gov/FinancialDisclosure
3. **Strategy Type**: Weekly rebalancing with position sizing based on congressional investment amounts
4. **Backtesting**: Multi-year historical analysis with comprehensive performance metrics

---

## 📊 Current Data Status

### ✅ Successfully Completed:
- **Multi-year PDF downloads**: Historical data from 2022-2025
- **PDF processing**: Extracted trading data from ~300+ congressional disclosure PDFs
- **Data consolidation**: All trades compiled into `stock_purchases/all_purchases` CSV file
- **Ticker mapping**: Stock names mapped to trading symbols via `mappings/all_stocks.csv`

### 📈 Dataset Statistics:
- **Total Records**: ~3,900+ congressional trading transactions
- **Date Range**: 2022 to 2025 (multi-year coverage)
- **Unique Congress Members**: 50+ active traders
- **Unique Stock Tickers**: 200+ different stocks
- **File Size**: Several MB of consolidated trading data

### ⚠️ Known Data Quality Issues:
1. **Date Formatting Inconsistencies**: Some PDFs contain malformed dates (e.g., "D Sch Dist" instead of valid dates)
2. **Missing Ticker Mappings**: Some stock names don't have corresponding ticker symbols
3. **Amount Field Variations**: Inconsistent formatting in min/max amount fields
4. **PDF Extraction Errors**: Some PDFs have formatting issues during text extraction
5. **"Out of Scope" Entries**: Non-stock investments (bonds, crypto, etc.) marked as "out of scope"

---

## 🏗️ Project Structure

```
PelosiForThePeople-master/
├── 📁 stock_purchases/
│   ├── 📁 07_25_2025/          # Recent PDFs (6 files)
│   ├── 📁 07_27_2025/          # Historical PDFs (293 files)
│   └── 📄 all_purchases        # ⭐ MAIN DATASET - Consolidated CSV
├── 📁 mappings/
│   └── 📄 all_stocks.csv       # Stock name to ticker mapping
├── 📁 financial_disclosures/   # Raw disclosure text files
├── 📁 other_documents/         # Non-stock related documents
├── 📄 compare_dates.py         # ⭐ PDF download & processing engine
├── 📄 load_trades.py           # ⭐ PDF parsing & data extraction
├── 📄 daily_run.py             # ⭐ Main orchestration script
├── 📄 read_pdf.py              # PDF text extraction utilities
├── 📄 data_utils.py            # Configuration & utilities
├── 📄 requirements.txt         # Python dependencies
├── 📄 us_congress_strat.ipynb  # ⭐ Main backtesting notebook
├── 📄 data_exploration_fixed.ipynb # ⭐ Data analysis notebook
└── 📄 congressional_trades_analysis.ipynb # Original analysis notebook
```

---

## 🔧 Technical Implementation

### Core Components:

#### 1. **Data Download System** (`compare_dates.py`)
- **Multi-year downloads**: Automatically downloads ZIP files for years 2022-2025
- **Network resilience**: Retry logic with timeout handling for connection issues
- **Incremental updates**: Only downloads new PDFs, skips existing ones
- **Configurable years**: `TARGET_YEAR` variable controls download scope

**Key Functions**:
- `download_historical_data()`: Downloads multi-year ZIP files
- `run_historical()`: Orchestrates historical data collection
- `get_response()`: Handles individual PDF downloads with retry logic

#### 2. **PDF Processing Engine** (`load_trades.py`)
- **Batch processing**: Processes all PDFs in stock_purchases folders
- **Data extraction**: Extracts representative name, stock info, dates, amounts
- **Ticker mapping**: Maps stock names to trading symbols
- **Data cleaning**: Handles malformed dates and invalid entries

**Key Functions**:
- `get_and_format_all_trades()`: Processes all PDFs into unified dataset
- `add_tickers()`: Maps stock names to ticker symbols
- `get_specific_trades()`: Processes daily/specific date trades

#### 3. **Main Orchestration** (`daily_run.py`)
- **Workflow coordination**: Manages data processing → download → notification sequence
- **File generation**: Creates/updates the `all_purchases` consolidated file
- **Telegram integration**: Optional notifications (currently has token issues)

**Critical Workflow Issue**: The script generates `all_purchases` BEFORE downloading new PDFs, requiring re-run after downloads to include new data.

---

## 📈 Data Structure

### `all_purchases` CSV Format:
```csv
representative_name,stock_name,buy_sell_flag,purchase_date,notification_date,min_amount,max_amount,ticker
```

**Column Descriptions**:
- `representative_name`: Congress member name (e.g., "ShreveJefferson")
- `stock_name`: Full company name (e.g., "Tesla, Inc. - Common Stock (TSLA)")
- `buy_sell_flag`: Transaction type ("P" = Purchase, "S" = Sale)
- `purchase_date`: Transaction date (YYYY-MM-DD format)
- `notification_date`: Disclosure date (MM/DD/YYYY format)
- `min_amount`: Minimum transaction amount ($)
- `max_amount`: Maximum transaction amount ($)
- `ticker`: Stock symbol (e.g., "TSLA") or "out of scope" for non-stocks

---

## 🚀 Usage Workflow

### For Data Collection:
```powershell
# 1. Download historical data (multi-year)
python -c "import compare_dates; compare_dates.run_historical()"

# 2. Process all PDFs into consolidated dataset
python daily_run.py

# 3. Explore the data
jupyter notebook data_exploration_fixed.ipynb
```

### For Backtesting:
```powershell
# Run the main strategy notebook
jupyter notebook us_congress_strat.ipynb
```

---

## 🛠️ Environment Setup

### Dependencies (`requirements.txt`):
```
requests==2.31.0
pandas==2.0.3
numpy==1.24.3
matplotlib==3.7.2
seaborn==0.12.2
jupyter==1.0.0
python-telegram-bot==20.3
PyPDF2==3.0.1
yfinance==0.2.18
```

### Virtual Environment:
```powershell
# Create and activate
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

---

## 📊 Backtesting Results (Previous Run)

### Strategy Performance:
- **Total Return**: 11.69%
- **Annualized Return**: 17.15%
- **Sharpe Ratio**: 1.27
- **Maximum Drawdown**: -4.92%
- **Backtest Period**: 2024-11-11 to 2025-07-25 (~8 months)
- **Initial Capital**: $100,000
- **Final Value**: $111,686.89

### Strategy Details:
- **Rebalancing**: Weekly (Fridays)
- **Position Sizing**: Weighted by congressional investment amounts
- **Universe**: Stocks with valid tickers from congressional trades
- **Benchmark**: Can be compared against S&P 500 or other indices

---

## ⚠️ Current Issues & Limitations

### 1. **Data Quality Problems**:
- **Invalid dates**: Some PDFs contain non-date text in date fields
- **Missing tickers**: Not all stock names have corresponding ticker symbols
- **Inconsistent formatting**: PDF extraction produces varied data formats
- **Amount field issues**: Some transactions have missing or malformed amounts

### 2. **Technical Issues**:
- **Workflow sequence**: `all_purchases` generated before new downloads
- **Telegram notifications**: Invalid/missing bot token causes errors (non-blocking)
- **PDF parsing errors**: Some PDFs have formatting that breaks extraction

### 3. **Data Processing Fixes Applied**:
- **Date handling**: Added `errors='coerce'` for malformed dates
- **Filtering**: Remove records with invalid dates from analysis
- **Error reporting**: Show which records are excluded and why

---

## 🔄 Next Steps & Recommendations

### Immediate Actions:
1. **Data Quality Enhancement**:
   - Improve PDF text extraction for better date/amount parsing
   - Expand ticker mapping database for missing stock symbols
   - Add data validation rules for amount fields

2. **Workflow Optimization**:
   - Fix `daily_run.py` sequence to generate `all_purchases` AFTER downloads
   - Add automated data quality checks and reporting
   - Implement better error handling for malformed PDFs

3. **Strategy Enhancement**:
   - Add transaction costs and slippage modeling
   - Implement position limits and risk management
   - Add benchmark comparison and attribution analysis

### Advanced Features:
1. **Real-time Implementation**:
   - Set up automated daily data collection
   - Implement live trading signal generation
   - Add portfolio management and execution systems

2. **Analysis Expansion**:
   - Member-specific performance analysis
   - Sector and industry breakdowns
   - Timing analysis (disclosure lag effects)

---

## 📁 Key Files for Continuation

### Essential Files:
1. **`stock_purchases/all_purchases`** - Main dataset (3,900+ records)
2. **`data_exploration_fixed.ipynb`** - Data analysis notebook (works with current structure)
3. **`us_congress_strat.ipynb`** - Main backtesting notebook
4. **`compare_dates.py`** - Data download engine (enhanced with multi-year support)
5. **`load_trades.py`** - PDF processing engine (enhanced with error handling)

### Configuration Files:
- **`requirements.txt`** - All dependencies installed and working
- **`mappings/all_stocks.csv`** - Stock name to ticker mapping
- **`data_utils.py`** - Contains configuration variables

---

## 🎯 Project Status Summary

### ✅ **Completed Successfully**:
- Multi-year historical data collection (2022-2025)
- PDF processing and data extraction
- Data consolidation into unified CSV format
- Basic backtesting framework with proven results
- Data exploration and analysis tools
- Error handling for common data quality issues

### ⚠️ **Partially Complete**:
- Data quality improvements (ongoing issue with PDF extraction)
- Ticker mapping (some stocks still unmapped)
- Workflow optimization (sequence issue in daily_run.py)

### 🔄 **Ready for Next Phase**:
- Enhanced data cleaning and validation
- Advanced backtesting features
- Real-time implementation
- Production deployment considerations

---

## 💡 Key Insights for Continuation

1. **Data is Available**: The core dataset is complete and usable for backtesting
2. **Quality Over Quantity**: Focus on improving data quality rather than collecting more data
3. **Proven Strategy**: The basic congressional following strategy shows positive results
4. **Scalable Framework**: The infrastructure can handle larger datasets and more complex strategies
5. **Known Issues**: All major problems are documented and have potential solutions

---

## 🔗 References & Resources

- **Data Source**: https://disclosures-clerk.house.gov/FinancialDisclosure
- **Strategy Inspiration**: Quiver Quant Congress Buys strategy
- **YouTube Reference**: https://www.youtube.com/watch?v=8X14fi5o2gY
- **Quiver Quant**: https://www.quiverquant.com/strategies/s/Congress%20Buys/

---

**Last Updated**: July 28, 2025  
**Project Status**: Data Collection Complete, Ready for Enhanced Processing  
**Next LLM Handoff**: Focus on data quality improvements and advanced backtesting features
