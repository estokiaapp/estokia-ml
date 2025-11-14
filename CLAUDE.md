# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

EstokIA ML is a machine learning project focused on stock prediction and inventory management. The project integrates with a Node.js/Fastify backend using Prisma ORM and SQLite database. Python scripts analyze sales data from the shared database and generate demand forecasts using linear regression and time series analysis.

## Key Components

### Core Files
- `sales_prediction.py` - Main SalesPredictionDB class implementing per-user demand forecasting with database integration
- `run_daily_predictions.py` - Automated scheduler for running predictions across all active users
- `setup_cron.sh` - Cron job installation script for 3x daily automated predictions
- `linear_regression.ipynb` - Jupyter notebook with historical sales analysis and linear regression implementation

### Database Integration
- **Database**: SQLite (`../estokia-backend/prisma/dev.db`)
- **Schema**: Managed by Prisma ORM in the backend project
- **Tables Used**:
  - `sales` - Sale transactions (user_id, sale_date, status)
  - `sale_items` - Individual sale line items (product_id, quantity, unit_price)
  - `products` - Product catalog (current_stock, minimum_stock)
  - `demand_forecasts` - ML-generated predictions (UPSERT strategy, one row per user+product)

### SalesPredictionDB Class Architecture
The main `SalesPredictionDB` class provides:
- **Database Loading**: Direct SQLite queries with user-specific filtering
- **Product Data**: Loads current stock levels from products table for stockout calculations
- **Demand Calculation**: Average daily demand calculation with time-based features (day_of_week, month, days_since_start)
- **Stockout Prediction**: Time-based prediction using `current_stock / daily_demand`
- **Confidence Levels**: Based on unique sale dates (VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH)
- **Model Training**: Linear regression per product with R² evaluation
- **Future Predictions**: 30-day demand forecasting with visualization
- **Database Persistence**: UPSERT strategy with Prisma-compatible ISO 8601 dates
- **Type Safety**: Helper functions to prevent NaN/inf values in database

## Development Environment

### Python Setup
- Python 3.13.2
- Virtual environment located in `venv/` directory
- Dependencies include: pandas, numpy, scikit-learn, matplotlib

### Running the Code
```bash
# Activate virtual environment
source venv/bin/activate

# Run predictions for specific user
python sales_prediction.py 1

# Run predictions for all active users (recommended)
python run_daily_predictions.py

# Start Jupyter notebook for interactive analysis
jupyter notebook linear_regression.ipynb
```

### Database Schema (Prisma-Managed)
The system queries the following tables:

**sales** - Sale transactions
- `id`, `user_id`, `sale_date` (Unix ms timestamp), `status` (PENDING, COMPLETED, CANCELLED)

**sale_items** - Sale line items
- `id`, `sale_id`, `product_id`, `quantity`, `unit_price`, `created_at`

**products** - Product catalog
- `id`, `name`, `sku`, `current_stock`, `minimum_stock`, `active`

**demand_forecasts** - ML predictions (written by Python)
- `id`, `product_id`, `user_id` (required)
- `days_to_stockout` (Int? - calculated from current_stock/daily_demand)
- `average_daily_demand` (Float? - must not be NaN/inf)
- `confidence_level` (Enum: VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH)
- `historical_data` (JSON string with records/unique_dates/date_range)
- `calculation_date`, `created_at` (ISO 8601 format: YYYY-MM-DDTHH:MM:SS.000Z)

## Key Algorithms

### Demand Prediction
Uses historical sales data aggregated by product and date. Features include:
- `days_since_start` - Days elapsed since first sale
- `day_of_week` - Weekday pattern (0=Monday, 6=Sunday)
- `month` - Monthly seasonality
- Linear regression trained per product
- Average daily demand calculated from historical quantities

### Stockout Prediction
**FIXED**: Now correctly retrieves `current_stock` from `products` table (not `sale_items`)
- Formula: `days_to_stockout = current_stock / average_daily_demand`
- Returns `None` if no stock data or zero demand
- Converted to `Int` (rounded) for Prisma compatibility

### Confidence Levels
Based on unique sale dates (not total records):
- **VERY_HIGH**: ≥60 unique dates
- **HIGH**: 30-59 unique dates
- **MEDIUM**: 15-29 unique dates
- **LOW**: 8-14 unique dates
- **VERY_LOW**: <8 unique dates

### Type Safety & Prisma Compatibility
Helper functions prevent database errors:
- `to_int_or_none()` - Converts floats to int, filters NaN/inf → NULL
- `to_float_or_none()` - Validates floats, filters NaN/inf → NULL
- ISO 8601 datetime format: `YYYY-MM-DDTHH:MM:SS.000Z`
- UPSERT strategy: One forecast per user+product (unique constraint)

## Common Tasks

### Resetting Database and Regenerating Forecasts
```bash
# Backend directory
cd /Users/gkanawati/Documents/GitHub/estokia/estokia-backend

# Reset database (drops data, runs migrations, seeds)
npx prisma migrate reset

# Or just run seed
npx prisma db seed

# ML directory - regenerate forecasts
cd /Users/gkanawati/Documents/GitHub/estokia/estokia-ml
source venv/bin/activate
python run_daily_predictions.py
```

### Modifying Prediction Logic
Core methods in `SalesPredictionDB` class:
- `load_data()` - Query sales data for specific user
- `load_products()` - **NEW**: Load current stock from products table
- `prepare_data()` - Aggregate sales by product+date, add time features
- `train_model(product_id)` - Linear regression with R² evaluation
- `calculate_confidence_level(num_records)` - Map data points to enum
- `insert_demand_forecasts()` - UPSERT with type safety and ISO 8601 dates

### Debugging Prisma P2023 Errors
If you see "Conversion failed: input contains invalid characters":
1. Check `calculation_date` and `created_at` use ISO 8601 format (with `T` and `Z`)
2. Verify no NaN/inf values in `days_to_stockout` or `average_daily_demand`
3. Ensure `confidence_level` matches enum values exactly
4. Clear bad data: `DELETE FROM demand_forecasts;` then re-run predictions

### Scheduled Predictions
Set up automated 3x daily forecasts:
```bash
./setup_cron.sh  # Installs cron jobs at 02:00, 08:00, 17:30
tail -f predictions.log  # Monitor execution
```

See `SCHEDULED_PREDICTIONS.md` for detailed setup.