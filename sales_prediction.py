import pandas as pd
import numpy as np
import math
from datetime import datetime, timedelta, timezone
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

DB_PATH = '/Users/gkanawati/Documents/GitHub/estokia/estokia-backend/prisma/dev.db'

def to_int_or_none(value):
    """
    Convert a value to int or None, handling NaN/inf/invalid values.

    Args:
        value: Any numeric or None value

    Returns:
        int or None: Rounded integer or None if invalid
    """
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return int(round(f))

def to_float_or_none(value):
    """
    Convert a value to float or None, handling NaN/inf/invalid values.

    Args:
        value: Any numeric or None value

    Returns:
        float or None: Float value or None if NaN/inf/invalid
    """
    if value is None:
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f

class SalesPredictionDB:

    def __init__(self, db_path=DB_PATH, user_id=3):
        self.db_path = db_path
        self.user_id = user_id
        self.conn = None
        self.products = None
        self.sales = None
        self.stock = None
        self.demand_forecast = None

    def connect_db(self):
        """Connect to the SQLite database"""
        import sqlite3
        self.conn = sqlite3.connect(self.db_path)

    def load_data(self):
        """Load data from the database into pandas DataFrames for a specific user"""
        self.connect_db()
        self.sale_items = pd.read_sql(
            """
                SELECT si.*, s.sale_date, p.name AS product_name
                FROM sale_items si
                INNER JOIN sales s ON si.sale_id = s.id
                INNER JOIN products p ON si.product_id = p.id
                WHERE s.user_id=?
                AND s.status='COMPLETED'
            """,
            self.conn,
            params=(self.user_id,)
        )

        self.conn.close()

        print(f"Data loaded successfully for user_id={self.user_id}")
        print(f"Sale Items length: {len(self.sale_items)}")
        print(self.sale_items.head())

    def load_products(self):
        """Load products data to get current stock levels"""
        self.connect_db()
        self.products = pd.read_sql(
            """
                SELECT id, name, sku, current_stock, minimum_stock
                FROM products
                WHERE active=1
            """,
            self.conn
        )
        self.conn.close()
        print(f"Products loaded: {len(self.products)}")

    def prepare_data(self):
        """Prepare data for sales prediction - unified DataFrame approach"""
        # Use sale_items which already includes sale_date (selected in load_data)
        if not hasattr(self, 'sale_items') or self.sale_items is None:
            print("Error: sale_items not loaded. Run load_data() first.")
            return None

        product_sales = self.sale_items.copy()
        if product_sales.empty:
            return None

        # Ensure sale_date exists and is datetime
        if 'sale_date' not in product_sales.columns:
            print("Error: sale_date column not found in sale_items.")
            return None

        # Convert from Unix timestamp in milliseconds to datetime
        product_sales['sale_date'] = pd.to_datetime(product_sales['sale_date'], unit='ms').dt.normalize()

        print('~ prepare_data - Merged product_sales: \n', product_sales)

        # Group by product_id and sale_date, sum quantities
        sales_aggregated = product_sales.groupby(['product_id', 'sale_date']).agg({'quantity': 'sum'}).reset_index()

        print('~ prepare_data - Aggregated sales_aggregated: \n', sales_aggregated)

        # Add time-based features for better predictions
        sales_aggregated['day_of_week'] = sales_aggregated['sale_date'].dt.dayofweek
        sales_aggregated['day_of_month'] = sales_aggregated['sale_date'].dt.day
        sales_aggregated['month'] = sales_aggregated['sale_date'].dt.month
        sales_aggregated['days_since_start'] = (
            sales_aggregated['sale_date'] - sales_aggregated['sale_date'].min()
        ).dt.days

        sales_aggregated = sales_aggregated.sort_values(['product_id', 'sale_date'])

        print("=" * 100)
        print(f'\nShape: {sales_aggregated.shape}')
        print(sales_aggregated.head(20))

        return sales_aggregated

    def train_model(self, product_id):
        """
        Train a sales prediction model for a specific product

        Args:
            product_id: ID of the product to train model for

        Returns:
            dict: Contains the trained model and training information
        """
        if self.demand_forecast is None:
            print("Error: Run prepare_data() first")
            return None

        # Filter data for specific product
        product_data = self.demand_forecast[self.demand_forecast['product_id'] == product_id].copy()

        if product_data.empty:
            print(f"No data found for product_id={product_id}")
            return None

        print(f"\n{'='*80}")
        print(f"Training model for product_id={product_id}")
        print(f"{'='*80}")
        print(f"Total records: {len(product_data)}")
        print(f"Date range: {product_data['sale_date'].min()} to {product_data['sale_date'].max()}")

        # Prepare features (X) and target (y)
        X = product_data[['days_since_start', 'day_of_week', 'month']].values
        y = product_data['quantity'].values

        # Train the model
        modelo = LinearRegression().fit(X, y)

        # Generate predictions for historical data (for validation)
        y_pred = modelo.predict(X)

        print(f"\nModel trained successfully!")
        print(f"Coefficients: {modelo.coef_}")
        print(f"Intercept: {modelo.intercept_:.4f}")

        return {
            'model': modelo,
            'product_id': product_id,
            'product_data': product_data,
            'X': X,
            'y': y,
            'y_pred': y_pred
        }

    def evaluate_model(self, trained_model):
        """
        Evaluate model performance using R², MAE, and MAPE metrics

        Args:
            trained_model: Dictionary returned from train_model()

        Returns:
            dict: Performance metrics
        """
        if trained_model is None:
            print("Error: No trained model provided")
            return None

        y_true = trained_model['y']
        y_pred = trained_model['y_pred']

        # Calculate metrics
        r2 = r2_score(y_true=y_true, y_pred=y_pred)
        mae = mean_absolute_error(y_true=y_true, y_pred=y_pred)

        # Calculate MAPE manually (to handle zero values)
        mask = y_true != 0
        if mask.sum() > 0:
            mape = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
        else:
            mape = 0.0

        print(f"\n{'='*80}")
        print(f"Model Evaluation - Product ID: {trained_model['product_id']}")
        print(f"{'='*80}")
        print(f"R² (R-squared):               {r2*100:.2f}% - Model explains {r2*100:.2f}% of variance")
        print(f"MAE (Mean Absolute Error):    {mae:.4f} units")
        print(f"MAPE (Mean Absolute % Error): {mape:.2f}%")

        # Interpretation
        if r2 > 0.7:
            quality = "Excellent"
        elif r2 > 0.5:
            quality = "Good"
        elif r2 > 0.3:
            quality = "Fair"
        else:
            quality = "Poor"

        print(f"\nModel Quality: {quality}")
        print(f"{'='*80}")

        return {
            'r2': r2,
            'mae': mae,
            'mape': mape,
            'quality': quality
        }

    def predict_future(self, trained_model, days_ahead=30):
        """
        Predict future demand for the next N days

        Args:
            trained_model: Dictionary returned from train_model()
            days_ahead: Number of days to predict into the future

        Returns:
            DataFrame: Future predictions with dates and quantities
        """
        if trained_model is None:
            print("Error: No trained model provided")
            return None

        product_data = trained_model['product_data']
        modelo = trained_model['model']

        # Get the last date in training data
        last_date = product_data['sale_date'].max()
        last_days_since_start = product_data['days_since_start'].max()

        # Generate future dates
        future_dates = pd.date_range(
            start=last_date + timedelta(days=1),
            periods=days_ahead,
            freq='D'
        )

        # Create features for future dates
        future_data = pd.DataFrame({
            'sale_date': future_dates,
            'days_since_start': range(last_days_since_start + 1, last_days_since_start + days_ahead + 1),
            'day_of_week': future_dates.dayofweek,
            'month': future_dates.month
        })

        # Prepare features for prediction
        X_future = future_data[['days_since_start', 'day_of_week', 'month']].values

        # Make predictions
        future_predictions = modelo.predict(X_future)

        # Ensure predictions are non-negative
        future_predictions = np.maximum(future_predictions, 0)

        # Add predictions to DataFrame
        future_data['predicted_quantity'] = future_predictions

        print(f"\n{'='*80}")
        print(f"Future Predictions - Product ID: {trained_model['product_id']}")
        print(f"{'='*80}")
        print(f"Predicting from {future_dates[0].date()} to {future_dates[-1].date()}")
        print(f"\nFirst 10 predictions:")
        print(future_data[['sale_date', 'predicted_quantity']].head(10))
        print(f"\nAverage predicted demand: {future_predictions.mean():.2f} units/day")
        print(f"Total predicted demand: {future_predictions.sum():.2f} units")
        print(f"{'='*80}")

        return future_data

    def calculate_confidence_level(self, num_records):
        """
        Calculate confidence level based on number of historical records

        Args:
            num_records: Number of unique sale dates for the product

        Returns:
            str: Confidence level (VERY_LOW, LOW, MEDIUM, HIGH, VERY_HIGH)
        """
        if num_records < 8:
            return 'VERY_LOW'
        elif num_records < 15:
            return 'LOW'
        elif num_records < 30:
            return 'MEDIUM'
        elif num_records < 60:
            return 'HIGH'
        else:
            return 'VERY_HIGH'

    def insert_demand_forecasts(self, db_path, demand_forecasts_df):
        """Insert or update demand forecast rows using SQLite UPSERT.

        Maintains one record per user+product combination, updating on each run.
        Ensures all values are Prisma-compatible (ISO 8601 dates, no NaN/inf).

        demand_forecasts_df: DataFrame with columns [product_id, days_to_stockout, average_daily_demand, confidence_level, historical_data]
        """
        import sqlite3
        import json

        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()

            # Ensure unique constraint exists (idempotent operation)
            cur.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS
                demand_forecasts_user_product_unique
                ON demand_forecasts(user_id, product_id)
            """)

            # Use ISO 8601 format for Prisma compatibility
            now = datetime.now(timezone.utc)
            now_ts = now.strftime('%Y-%m-%dT%H:%M:%S.000Z')  # Full timestamp with time
            calc_date = now.replace(hour=0, minute=0, second=0, microsecond=0)\
                           .strftime('%Y-%m-%dT%H:%M:%S.000Z')  # Start of day

            for _, row in demand_forecasts_df.iterrows():
                # Convert days_to_stockout to Int or None (Prisma expects Int?, not Float)
                days_to_stockout = to_int_or_none(row.get('days_to_stockout'))

                # Convert average_daily_demand to Float or None (no NaN/inf)
                avg_daily_demand = to_float_or_none(row.get('average_daily_demand'))

                # Convert historical_data dict to proper JSON string
                historical_data = None
                if row.get('historical_data') is not None:
                    historical_data = json.dumps(row.get('historical_data'))

                cur.execute(
                    """
                    INSERT INTO demand_forecasts (
                        product_id, user_id, days_to_stockout, average_daily_demand,
                        confidence_level, historical_data, calculation_date, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(user_id, product_id) DO UPDATE SET
                        days_to_stockout = excluded.days_to_stockout,
                        average_daily_demand = excluded.average_daily_demand,
                        confidence_level = excluded.confidence_level,
                        historical_data = excluded.historical_data,
                        calculation_date = excluded.calculation_date,
                        created_at = excluded.created_at
                    """,
                    (
                        row.get('product_id'),
                        self.user_id,
                        days_to_stockout,
                        avg_daily_demand,
                        row.get('confidence_level'),
                        historical_data,
                        calc_date,
                        now_ts,
                    ),
                )

            conn.commit()
            conn.close()
            print(f"✓ Upserted {len(demand_forecasts_df)} demand forecasts for user_id={self.user_id}")
        except Exception as e:
            print(f"✗ Failed to upsert demand forecasts into {db_path}: {e}")

def main():
    """Example usage of the SalesPredictionDB class - Full workflow demonstration"""
    import sys

    # Check if user_id was provided as command-line argument
    user_id = 3  # Default user_id (Admin User)
    if len(sys.argv) > 1:
        try:
            user_id = int(sys.argv[1])
        except ValueError:
            print(f"Error: Invalid user_id '{sys.argv[1]}'. Using default user_id={user_id}")

    # Step 1: Initialize predictor with user_id
    predictor = SalesPredictionDB(user_id=user_id)

    # Step 2: Load data from database
    predictor.load_data()

    # Step 2b: Load products data for current stock levels
    predictor.load_products()

    # Step 3: Prepare data for training
    predictor.demand_forecast = predictor.prepare_data()

    if predictor.demand_forecast is None or predictor.demand_forecast.empty:
        print("No data available for training")
        return

    # Get unique product IDs
    product_ids = predictor.demand_forecast['product_id'].unique()
    print(f"\nFound {len(product_ids)} products: {product_ids}")

    # Step 4: Train model for each product
    for product_id in product_ids:
        print(f"\n{'#'*80}")
        print(f"# Processing Product ID: {product_id}")
        print(f"{'#'*80}")

        # Train model
        trained_model = predictor.train_model(product_id)

        if trained_model is None:
            continue

        # Evaluate model
        metrics = predictor.evaluate_model(trained_model)

        # Predict future (next 30 days)
        future_predictions = predictor.predict_future(trained_model, days_ahead=30)

        print(f"\n{'#'*80}\n")

    # After processing all products, persist a summary of forecasts
    # Build a DataFrame with one row per product using the last trained model outputs
    rows = []
    for product_id in product_ids:
        prod_data = predictor.demand_forecast[predictor.demand_forecast['product_id'] == product_id]
        if prod_data.empty:
            continue

        # Use predict_stockout-like logic: estimate avg daily demand and days to stockout
        avg_daily = prod_data['quantity'].mean()

        # Get current_stock from products table
        product_row = predictor.products[predictor.products['id'] == product_id]
        if not product_row.empty:
            current_stock = int(product_row.iloc[0]['current_stock'])
        else:
            current_stock = None

        days_to_stockout = None
        if avg_daily and current_stock is not None and avg_daily > 0:
            days_to_stockout = current_stock / avg_daily

        # Calculate number of unique dates for confidence
        num_unique_dates = prod_data['sale_date'].nunique()

        hist_summary = {
            'records': int(len(prod_data)),
            'unique_dates': int(num_unique_dates),
            'start_date': str(prod_data['sale_date'].min().date()),
            'end_date': str(prod_data['sale_date'].max().date())
        }

        # Calculate confidence based on data points
        confidence = predictor.calculate_confidence_level(num_unique_dates)

        rows.append({
            'product_id': product_id,
            'days_to_stockout': days_to_stockout,
            'average_daily_demand': avg_daily,
            'confidence_level': confidence,
            'historical_data': hist_summary,
        })

    if rows:
        df_forecasts = pd.DataFrame(rows)
        predictor.insert_demand_forecasts(DB_PATH, df_forecasts)

if __name__ == "__main__":
    main()