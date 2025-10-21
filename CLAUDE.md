# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EstokIA ML is a machine learning project focused on stock prediction and inventory management. The project contains Python scripts for analyzing sales data and predicting stock levels using linear regression and time series analysis.

## Key Components

### Core Files
- `stock_prediction.py` - Main StockPrediction class implementing demand forecasting, stockout prediction, and alert generation
- `linear_regression.ipynb` - Jupyter notebook with historical sales analysis and linear regression implementation
- `data/estokia_sales_data.csv` - Primary sales dataset with product information, sales history, and current stock levels
- `data/historico_vendas.csv` - Historical sales data used for time series analysis

### StockPrediction Class Architecture
The main `StockPrediction` class provides:
- **Data Loading**: CSV parsing with date conversion and error handling
- **Demand Calculation**: Average daily demand calculation with configurable lookback periods
- **Stockout Prediction**: Time-based prediction of when products will run out of stock
- **Trend Analysis**: Linear regression-based demand trend forecasting
- **Alert System**: Priority-based stock alert generation (CRITICAL, HIGH, MEDIUM, LOW)
- **Visualization**: Matplotlib-based plotting for sales history and trends

## Development Environment

### Python Setup
- Python 3.13.2
- Virtual environment located in `venv/` directory
- Dependencies include: pandas, numpy, scikit-learn, matplotlib

### Running the Code
```bash
# Activate virtual environment
source venv/bin/activate

# Run main stock prediction analysis
python stock_prediction.py

# Start Jupyter notebook for interactive analysis
jupyter notebook linear_regression.ipynb
```

### Data Structure
The sales data CSV contains:
- `product_id` - Unique product identifier
- `product_name` - Product display name
- `sale_date` - Date of sale (YYYY-MM-DD format)
- `quantity_sold` - Number of units sold
- `current_stock` - Current inventory level
- `minimum_stock` - Minimum stock threshold
- Additional fields: sku, category, unit_price, supplier

## Key Algorithms

### Demand Prediction
Uses historical sales data to calculate average daily demand over a specified lookback period. For products with limited history, falls back to single-sale estimates.

### Stockout Prediction
Calculates days until stockout using: `current_stock / daily_demand`
Confidence levels based on available data points:
- HIGH: ≥20 sales records
- MEDIUM: 10-19 sales records
- LOW: <10 sales records

### Trend Analysis
Implements linear regression on time-series sales data to identify demand trends (increasing/decreasing) and predict future demand patterns.

## Common Tasks

### Adding New Products
When adding new product analysis, ensure the CSV data includes all required fields and that `product_id` values are unique.

### Modifying Prediction Logic
The core prediction algorithms are in the `StockPrediction` class methods:
- `calculate_daily_demand()` - Modify for different demand calculation approaches
- `predict_stockout_date()` - Adjust confidence thresholds or calculation logic
- `predict_demand_trend()` - Change regression model or forecasting period

### Data Analysis
Use the Jupyter notebook for exploratory data analysis and testing new prediction models before integrating into the main Python script.