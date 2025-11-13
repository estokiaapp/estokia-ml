# EstokIA ML - Intelligent Stock Prediction System

[![Python](https://img.shields.io/badge/Python-3.13.2-blue.svg)](https://python.org)
[![Machine Learning](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)](https://scikit-learn.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

EstokIA ML is an intelligent inventory management system that uses machine learning to predict stock levels, forecast demand, and generate automated alerts for inventory optimization. Built with Python and scikit-learn, it helps businesses prevent stockouts and optimize their inventory management strategies.

## 🚀 Features

- **📊 Demand Forecasting**: Predict future product demand using historical sales data
- **⏰ Stockout Prediction**: Calculate when products will run out of stock with confidence intervals
- **📈 Trend Analysis**: Identify demand trends (increasing/decreasing) using linear regression
- **🚨 Smart Alerts**: Generate priority-based stock alerts (Critical, High, Medium, Low)
- **📊 Data Visualization**: Interactive plots for sales history and demand trends
- **🔍 Comprehensive Analysis**: Analyze entire product catalogs automatically

## 📁 Project Structure

```
estokia-ml/
├── stock_prediction.py       # Main StockPrediction class
├── linear_regression.ipynb   # Jupyter notebook for analysis
├── data/
│   ├── estokia_sales_data.csv    # Primary sales dataset (138 records)
│   └── historico_vendas.csv      # Historical sales data
├── venv/                     # Virtual environment
├── CLAUDE.md                 # Development guidelines
└── README.md                 # This file
```

## 🛠️ Installation

### Prerequisites

- Python 3.13.2 or higher
- Virtual environment (recommended)

### Setup

1. **Clone the repository**

```bash
git clone <repository-url>
cd estokia-ml
```

2. **Create and activate virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**

```bash
pip install pandas numpy scikit-learn matplotlib jupyter
```

## 🎯 Quick Start

### Basic Usage

```python
from stock_prediction import StockPrediction

# Initialize the predictor
predictor = StockPrediction()

# Load your sales data
predictor.load_data('data/estokia_sales_data.csv')

# Predict stockout for a specific product
result = predictor.predict_stockout_date('PROD001', current_stock=25)
print(f"Product will run out in {result['days_to_stockout']} days")
print(f"Predicted stockout date: {result['stockout_date']}")
```

### Run Complete Analysis

```bash
python sales_prediction.py
```

This will analyze all products in the dataset and generate:

- Stockout predictions for each product
- Demand trend analysis
- Priority-based stock alerts

### Interactive Analysis

```bash
jupyter notebook linear_regression.ipynb
```

Open the Jupyter notebook for interactive data exploration and custom analysis.

## 📊 Data Format

The system expects CSV data with the following columns:

| Column          | Description               | Example                |
| --------------- | ------------------------- | ---------------------- |
| `product_id`    | Unique product identifier | PROD001                |
| `product_name`  | Product display name      | Notebook Acer Aspire 5 |
| `sale_date`     | Date of sale (YYYY-MM-DD) | 2024-08-01             |
| `quantity_sold` | Number of units sold      | 2                      |
| `current_stock` | Current inventory level   | 45                     |
| `minimum_stock` | Minimum stock threshold   | 5                      |
| `unit_price`    | Price per unit            | 2500.00                |
| `category`      | Product category          | Eletrônicos            |
| `supplier`      | Supplier name             | Acer Brasil            |

## 🔧 API Reference

### StockPrediction Class

#### Core Methods

**`load_data(csv_path)`**

- Loads sales data from CSV file
- Automatically converts dates and handles errors
- Returns: `bool` (success/failure)

**`predict_stockout_date(product_id, current_stock)`**

- Predicts when a product will run out of stock
- Returns: Dictionary with prediction details

```python
{
    'days_to_stockout': 12.5,
    'stockout_date': '2024-10-08',
    'daily_demand': 2.0,
    'confidence': 'HIGH',
    'message': 'Based on 25 sales records'
}
```

**`calculate_daily_demand(product_id, days_lookback=30)`**

- Calculates average daily demand for a product
- Returns: `float` (daily demand rate)

**`predict_demand_trend(product_id, days_ahead=30)`**

- Analyzes demand trends using linear regression
- Returns: Dictionary with trend analysis

**`generate_alerts(products_stock)`**

- Generates priority-based alerts for multiple products
- Input: Dictionary of `{product_id: current_stock}`
- Returns: List of alert dictionaries sorted by urgency

**`plot_product_analysis(product_id)`**

- Creates visualization plots for sales history and trends
- Displays: Historical sales and trend line analysis

## 📈 Alert System

The system generates four priority levels based on days until stockout:

| Priority        | Days Left | Alert Type         | Action Required     |
| --------------- | --------- | ------------------ | ------------------- |
| 🚨 **CRITICAL** | ≤ 3 days  | IMMEDIATE_STOCKOUT | Order immediately   |
| 🔴 **HIGH**     | 4-7 days  | URGENT_RESTOCK     | Plan urgent restock |
| 🟡 **MEDIUM**   | 8-14 days | PLAN_RESTOCK       | Schedule restock    |
| 🟢 **LOW**      | > 14 days | MONITOR_STOCK      | Continue monitoring |

## 📊 Confidence Levels

Predictions include confidence levels based on available data:

- **HIGH**: ≥20 sales records (most reliable)
- **MEDIUM**: 10-19 sales records (moderate reliability)
- **LOW**: <10 sales records (less reliable)

## 🎛️ Example Output

```
EstokIA Stock Prediction Analysis
==================================================

Product: Notebook Acer Aspire 5 (ID: PROD001)
Current Stock: 25
Days to Stockout: 12.5
Predicted Stockout Date: 2024-10-08
Daily Demand: 2.0
Confidence: HIGH
Demand Trend: decreasing (slope: -0.015)
Model Accuracy (R²): 0.847

==================================================
STOCK ALERTS
==================================================
🚨 CRITICAL - Product PROD003
   Product will run out in 2.1 days
   Confidence: MEDIUM

🔴 HIGH - Product PROD001
   Product will run out in 6.5 days
   Confidence: HIGH
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-algorithm`)
3. Commit your changes (`git commit -am 'Add new forecasting algorithm'`)
4. Push to the branch (`git push origin feature/new-algorithm`)
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- Create an [issue](../../issues) for bug reports or feature requests
- Check the [CLAUDE.md](CLAUDE.md) file for development guidelines
- Review the Jupyter notebook for usage examples

---

**EstokIA ML** - Making inventory management intelligent, one prediction at a time. 🎯
