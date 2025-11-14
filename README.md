# EstokIA ML - Intelligent Stock Prediction System

[![Python](https://img.shields.io/badge/Python-3.13.2-blue.svg)](https://python.org)
[![Machine Learning](https://img.shields.io/badge/ML-Scikit--Learn-orange.svg)](https://scikit-learn.org)
[![Database](https://img.shields.io/badge/Database-SQLite-blue.svg)](https://sqlite.org)
[![Prisma](https://img.shields.io/badge/Prisma-Compatible-brightgreen.svg)](https://prisma.io)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

EstokIA ML is an intelligent inventory management system that uses machine learning to predict stock levels, forecast demand, and generate automated alerts for inventory optimization. Integrated with a Node.js/Fastify backend using Prisma ORM and SQLite, it provides per-user demand forecasting with 3x daily automated predictions.

## 🚀 Features

- **📊 Demand Forecasting**: Predict future product demand using historical sales data with linear regression
- **👤 Per-User Predictions**: Isolated forecasts for each user with user-specific data filtering
- **⏰ Stockout Prediction**: Calculate when products will run out of stock (`current_stock / daily_demand`)
- **📈 Trend Analysis**: Time-based features (day_of_week, month, days_since_start) for seasonal patterns
- **🔒 Type Safety**: NaN/inf filtering with Prisma-compatible data types (Int?, Float?, Enum)
- **🗄️ Database Integration**: Direct SQLite queries with UPSERT strategy (one forecast per user+product)
- **⏱️ Scheduled Automation**: Cron jobs for 3x daily predictions (02:00, 08:00, 17:30)
- **🌐 REST API**: Prisma-powered endpoints for instant forecast retrieval
- **📊 Confidence Levels**: 5-tier system based on data quality (VERY_LOW to VERY_HIGH)

## 📁 Project Structure

```
estokia-ml/
├── sales_prediction.py           # Main SalesPredictionDB class (database-integrated)
├── run_daily_predictions.py      # Multi-user scheduler for automated predictions
├── setup_cron.sh                 # Cron job installer (3x daily automation)
├── linear_regression.ipynb       # Jupyter notebook for analysis
├── venv/                         # Virtual environment
├── predictions.log               # Execution logs from scheduled runs
├── cron.log                      # Cron job execution logs
├── CLAUDE.md                     # Development guidelines
├── README.md                     # This file
├── SCHEDULED_PREDICTIONS.md      # Detailed cron setup guide
├── CRON_QUICK_REFERENCE.md       # Quick command reference
├── SYSTEM_OVERVIEW.md            # Architecture documentation
├── SALES_VS_STOCK_COMPARISON.md  # Comparison guide
└── PREDICTION_CONFIDENCE_GUIDE.md # Data quality requirements

Database (shared with backend):
../estokia-backend/prisma/dev.db  # SQLite database managed by Prisma
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

### Basic Usage (Per-User Predictions)

```bash
# Activate virtual environment
source venv/bin/activate

# Run predictions for a specific user (e.g., user_id=1)
python sales_prediction.py 1

# Run predictions for all active users
python run_daily_predictions.py
```

**What happens:**
1. Loads sales data from SQLite database (filtered by user_id)
2. Loads product stock levels from products table
3. Trains linear regression model per product
4. Calculates `days_to_stockout = current_stock / average_daily_demand`
5. Assigns confidence level based on data quality (unique sale dates)
6. Upserts results into `demand_forecasts` table (one row per user+product)

**Database output:**
```sql
SELECT product_id, days_to_stockout, average_daily_demand, confidence_level
FROM demand_forecasts
WHERE user_id = 1;

-- Result:
-- product_id | days_to_stockout | average_daily_demand | confidence_level
-- 1          | 56               | 2.67                 | VERY_LOW
-- 2          | 16               | 5.00                 | VERY_LOW
-- 4          | 9                | 3.40                 | MEDIUM
```

### Scheduled Predictions (Recommended) ⭐

For production use, set up automatic predictions that run **3 times daily**:

```bash
# Easy setup with automated script
./setup_cron.sh

# Or test manually
python3 run_daily_predictions.py

# Monitor execution
tail -f cron.log
```

**Schedule:**

- 🌙 **02:00 AM** - Night processing (fresh morning data)
- ☀️ **08:00 AM** - Morning update (start of business)
- 🌆 **17:30 PM** - Evening update (end of business)

**Benefits:**

- ⚡ Instant API responses (pre-computed forecasts)
- 🎯 Consistent predictions for all users
- 📊 Multiple daily updates for fresh forecasts
- 📝 Comprehensive logging and error handling

See [SCHEDULED_PREDICTIONS.md](SCHEDULED_PREDICTIONS.md) for detailed setup or [CRON_QUICK_REFERENCE.md](CRON_QUICK_REFERENCE.md) for quick commands.

### Run Complete Analysis

```bash
source venv/bin/activate
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

## 📊 Database Schema (Prisma-Managed)

The system reads from and writes to a shared SQLite database managed by Prisma ORM:

### Tables Used

**sales** - Sale transactions
- `id` (INTEGER), `user_id` (INTEGER), `sale_date` (BIGINT - Unix ms), `status` (TEXT)
- Query: `WHERE user_id=? AND status='COMPLETED'`

**sale_items** - Individual line items
- `id`, `sale_id`, `product_id`, `quantity`, `unit_price`
- Joined with `sales` to get sale_date per user

**products** - Product catalog
- `id`, `name`, `sku`, `current_stock`, `minimum_stock`, `active`
- Used to fetch inventory levels for stockout calculation

**demand_forecasts** - ML predictions (written by Python)
- `product_id` (INTEGER), `user_id` (INTEGER) - Unique constraint
- `days_to_stockout` (INTEGER?) - Rounded from float, NULL if no stock data
- `average_daily_demand` (REAL?) - Validated float, NULL if NaN/inf
- `confidence_level` (TEXT) - Enum: VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH
- `historical_data` (TEXT) - JSON: `{"records": 10, "unique_dates": 8, ...}`
- `calculation_date` (TEXT) - ISO 8601: `2025-11-14T00:00:00.000Z`
- `created_at` (TEXT) - ISO 8601: `2025-11-14T10:30:15.000Z`

### Data Flow
```
SQLite DB → Python (sales_prediction.py) → demand_forecasts table → Prisma → Node.js API
```

## 🔧 API Reference

### SalesPredictionDB Class

#### Core Methods

**`__init__(db_path, user_id)`**
- Initializes predictor for specific user
- Parameters: `db_path` (str), `user_id` (int)

**`load_data()`**
- Loads sales data from SQLite for the specified user
- Queries: `sale_items` JOIN `sales` JOIN `products`
- Filters: `WHERE user_id=? AND status='COMPLETED'`

**`load_products()`**
- **NEW**: Loads product catalog with current stock levels
- Required for `days_to_stockout` calculation
- Queries: `SELECT id, current_stock, minimum_stock FROM products WHERE active=1`

**`prepare_data()`**
- Aggregates sales by product_id and sale_date
- Adds time-based features: `days_since_start`, `day_of_week`, `month`
- Converts Unix timestamps to datetime
- Returns: DataFrame ready for model training

**`train_model(product_id)`**
- Trains linear regression model for specific product
- Features: [days_since_start, day_of_week, month]
- Target: quantity sold
- Returns: Dictionary with model, data, predictions

**`evaluate_model(trained_model)`**
- Calculates R², MAE, MAPE metrics
- Returns: Dictionary with performance metrics
- Quality tiers: Poor (<0.3), Fair (0.3-0.5), Good (0.5-0.7), Very Good (0.7-0.85), Excellent (>0.85)

**`predict_future(trained_model, days_ahead=30)`**
- Generates 30-day demand forecast
- Returns: DataFrame with predicted quantities per day

**`calculate_confidence_level(num_records)`**
- Maps unique sale dates to confidence enum
- Returns: 'VERY_LOW', 'LOW', 'MEDIUM', 'HIGH', 'VERY_HIGH'

**`insert_demand_forecasts(db_path, demand_forecasts_df)`**
- Upserts forecasts into database with type safety
- Uses ISO 8601 datetime format
- Filters NaN/inf values
- UPSERT strategy: `ON CONFLICT(user_id, product_id) DO UPDATE`

#### Helper Functions

**`to_int_or_none(value)`**
- Safely converts float to int, handling NaN/inf
- Returns: `int` or `None`

**`to_float_or_none(value)`**
- Validates float values, filtering NaN/inf
- Returns: `float` or `None`

## 📊 Confidence Levels (Data Quality)

Predictions include confidence levels based on unique sale dates (not total records):

| Level            | Unique Dates | R² Expected | Reliability              | Use Case                          |
| ---------------- | ------------ | ----------- | ------------------------ | --------------------------------- |
| ✅ **VERY_HIGH** | ≥60 dates    | >0.85       | Excellent - Production   | Automated decisions, budgeting    |
| 🟢 **HIGH**      | 30-59 dates  | 0.70-0.85   | Very Good - Strategic    | Long-term planning, negotiations  |
| 🟡 **MEDIUM**    | 15-29 dates  | 0.50-0.70   | Good - Operational       | Short-term forecasts, reordering  |
| ⚠️ **LOW**       | 8-14 dates   | 0.30-0.50   | Fair - With Caution      | Rough estimates, combine with gut |
| ❌ **VERY_LOW**  | <8 dates     | <0.30       | Poor - Collect More Data | Not recommended for decisions     |

**Why unique dates matter:**
- 10 sales on 1 day = VERY_LOW confidence (no pattern detection)
- 10 sales over 10 days = LOW confidence (basic trend visible)
- 30 sales over 30 days = MEDIUM confidence (weekly patterns emerge)

See [PREDICTION_CONFIDENCE_GUIDE.md](PREDICTION_CONFIDENCE_GUIDE.md) for detailed analysis.

## 🎛️ Example Output

### Console Output (Python Script)
```
Data loaded successfully for user_id=1
Sale Items length: 73

Products loaded: 10

Training model for product_id=4
Total records: 15
Date range: 2025-08-19 to 2025-11-12

Model trained successfully!
Coefficients: [0.02 -0.15 0.08]
Intercept: 3.2450

Model Evaluation - Product ID: 4
R² (R-squared): 68.42% - Model explains 68.42% of variance
MAE (Mean Absolute Error): 1.2340 units
MAPE (Mean Absolute % Error): 28.45%
Model Quality: Good

✓ Upserted 9 demand forecasts for user_id=1
```

### Database Result
```sql
SELECT
  p.name,
  df.days_to_stockout,
  df.average_daily_demand,
  df.confidence_level,
  p.current_stock
FROM demand_forecasts df
JOIN products p ON df.product_id = p.id
WHERE df.user_id = 1
ORDER BY df.days_to_stockout ASC;

-- Critical alerts (low days_to_stockout):
-- Garden Hose      | 9 days  | 3.40 units/day | MEDIUM   | 30 stock
-- Denim Jeans      | 16 days | 5.00 units/day | VERY_LOW | 80 stock
-- Bluetooth Phones | 18 days | 2.50 units/day | LOW      | 45 stock
```

### API Response (GET /api/predictions/sales/1)
```json
{
  "user_id": 1,
  "total_forecasts": 9,
  "forecasts": [
    {
      "productId": 4,
      "daysToStockout": 9,
      "averageDailyDemand": 3.4,
      "confidenceLevel": "MEDIUM",
      "product": {
        "name": "Garden Hose",
        "currentStock": 30,
        "minimumStock": 8
      }
    }
  ]
}
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
