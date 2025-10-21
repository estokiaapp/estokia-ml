import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

DB_PATH = '/Users/gkanawati/Documents/GitHub/estokia/estokia-backend/prisma/dev.db'

class SalesPredictionDB:

    def __init__(self, db_path=DB_PATH, user_id=9):
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

        product_sales['sale_date'] = pd.to_datetime(product_sales['sale_date']).dt.normalize()

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

def main():
    """Example usage of the SalesPredictionDB class - Full workflow demonstration"""

    # Step 1: Initialize predictor
    predictor = SalesPredictionDB()

    # Step 2: Load data from database
    predictor.load_data()

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

if __name__ == "__main__":
    main()