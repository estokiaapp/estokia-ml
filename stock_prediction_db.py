import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class StockPredictionDB:
    def __init__(self):
        self.model = LinearRegression()
        self.predictions = {}
        self.products_df = None
        self.sales_df = None
        self.sale_items_df = None
        self.categories_df = None
        self.suppliers_df = None

    def load_data(self, data_folder='data/'):
        """Load all data from CSV files in database format"""
        try:
            # Load main tables
            self.products_df = pd.read_csv(f'{data_folder}products.csv')
            self.sales_df = pd.read_csv(f'{data_folder}sales.csv')
            self.sale_items_df = pd.read_csv(f'{data_folder}sale_items.csv')
            self.categories_df = pd.read_csv(f'{data_folder}categories.csv')
            self.suppliers_df = pd.read_csv(f'{data_folder}suppliers.csv')

            # Convert dates
            self.sales_df['sale_date'] = pd.to_datetime(self.sales_df['sale_date'])
            self.sale_items_df['created_at'] = pd.to_datetime(self.sale_items_df['created_at'])

            # Create the combined dataset for analysis
            self._create_analysis_dataset()
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False

    def _create_analysis_dataset(self):
        """Create a combined dataset for analysis similar to original format"""
        # Join sale_items with sales to get sale dates
        sales_items_with_dates = self.sale_items_df.merge(
            self.sales_df[['id', 'sale_date']],
            left_on='sale_id',
            right_on='id',
            suffixes=('', '_sale')
        )

        # Join with products to get product info and current stock
        self.df = sales_items_with_dates.merge(
            self.products_df[['id', 'name', 'sku', 'category_id', 'supplier_id', 'current_stock', 'minimum_stock']],
            left_on='product_id',
            right_on='id',
            suffixes=('', '_product')
        )

        # Join with categories and suppliers for complete info
        self.df = self.df.merge(
            self.categories_df[['id', 'name']],
            left_on='category_id',
            right_on='id',
            suffixes=('', '_category')
        )

        self.df = self.df.merge(
            self.suppliers_df[['id', 'name']],
            left_on='supplier_id',
            right_on='id',
            suffixes=('', '_supplier')
        )

        # Rename columns to match original format
        self.df = self.df.rename(columns={
            'product_id': 'product_id',
            'name': 'product_name',
            'name_category': 'category',
            'name_supplier': 'supplier',
            'quantity': 'quantity_sold',
            'unit_price': 'unit_price',
            'sale_date': 'sale_date'
        })

        # Select relevant columns
        self.df = self.df[['product_id', 'product_name', 'sku', 'category', 'sale_date',
                          'quantity_sold', 'unit_price', 'current_stock', 'minimum_stock', 'supplier']]

    def calculate_daily_demand(self, product_id, days_lookback=30):
        """Calculate average daily demand for a product"""
        product_data = self.df[self.df['product_id'] == product_id].copy()

        if len(product_data) == 0:
            return 0

        # Use all available data if we have recent sales
        recent_data = product_data.copy()

        if len(recent_data) == 0:
            return 0

        # Calculate total days span and total quantity
        if len(recent_data) > 1:
            start_date = recent_data['sale_date'].min()
            end_date = recent_data['sale_date'].max()
            total_days = (end_date - start_date).days + 1
            total_quantity = recent_data['quantity_sold'].sum()

            # Average daily demand over the period
            return total_quantity / total_days if total_days > 0 else 0
        else:
            # Single sale record - estimate daily demand as that quantity
            return recent_data['quantity_sold'].iloc[0]

    def predict_stockout_date(self, product_id, current_stock=None):
        """Predict when a product will run out of stock"""
        # Get current stock from products table if not provided
        if current_stock is None:
            product_info = self.products_df[self.products_df['id'] == product_id]
            if len(product_info) > 0:
                current_stock = product_info['current_stock'].iloc[0]
            else:
                return {
                    'days_to_stockout': None,
                    'stockout_date': None,
                    'daily_demand': 0,
                    'confidence': 'LOW',
                    'message': 'Product not found'
                }

        daily_demand = self.calculate_daily_demand(product_id)

        if daily_demand <= 0:
            return {
                'days_to_stockout': None,
                'stockout_date': None,
                'daily_demand': 0,
                'confidence': 'LOW',
                'message': 'No sales history available'
            }

        days_to_stockout = current_stock / daily_demand
        stockout_date = datetime.now() + timedelta(days=days_to_stockout)

        # Calculate confidence based on data quality
        product_data = self.df[self.df['product_id'] == product_id]
        data_points = len(product_data)

        if data_points >= 20:
            confidence = 'HIGH'
        elif data_points >= 10:
            confidence = 'MEDIUM'
        else:
            confidence = 'LOW'

        return {
            'days_to_stockout': round(days_to_stockout, 1),
            'stockout_date': stockout_date.strftime('%Y-%m-%d'),
            'daily_demand': round(daily_demand, 2),
            'confidence': confidence,
            'message': f'Based on {data_points} sales records'
        }

    def predict_demand_trend(self, product_id, days_ahead=30):
        """Predict demand trend using linear regression"""
        product_data = self.df[self.df['product_id'] == product_id].copy()

        if len(product_data) < 5:
            return None

        # Prepare data for regression
        product_data['days_since_start'] = (product_data['sale_date'] - product_data['sale_date'].min()).dt.days
        daily_sales = product_data.groupby(['days_since_start']).agg({
            'quantity_sold': 'sum'
        }).reset_index()

        if len(daily_sales) < 3:
            return None

        # Fit linear regression
        X = daily_sales[['days_since_start']]
        y = daily_sales['quantity_sold']

        self.model.fit(X, y)

        # Predict future demand
        last_day = daily_sales['days_since_start'].max()
        future_days = np.array([[last_day + i] for i in range(1, days_ahead + 1)])
        future_demand = self.model.predict(future_days)

        # Ensure non-negative predictions
        future_demand = np.maximum(future_demand, 0)

        return {
            'trend_slope': self.model.coef_[0],
            'avg_predicted_daily_demand': future_demand.mean(),
            'total_predicted_demand': future_demand.sum(),
            'r2_score': r2_score(y, self.model.predict(X)) if len(y) > 1 else 0
        }

    def generate_alerts(self, products_stock=None):
        """Generate stock alerts for products"""
        alerts = []

        # If no specific products provided, analyze all products
        if products_stock is None:
            products_stock = {}
            for _, product in self.products_df.iterrows():
                products_stock[product['id']] = product['current_stock']

        for product_id, current_stock in products_stock.items():
            prediction = self.predict_stockout_date(product_id, current_stock)

            if prediction['days_to_stockout'] is not None:
                days_left = prediction['days_to_stockout']

                # Generate alerts based on time remaining
                if days_left <= 3:
                    priority = 'CRITICAL'
                    alert_type = 'IMMEDIATE_STOCKOUT'
                elif days_left <= 7:
                    priority = 'HIGH'
                    alert_type = 'URGENT_RESTOCK'
                elif days_left <= 14:
                    priority = 'MEDIUM'
                    alert_type = 'PLAN_RESTOCK'
                else:
                    priority = 'LOW'
                    alert_type = 'MONITOR_STOCK'

                alerts.append({
                    'product_id': product_id,
                    'alert_type': alert_type,
                    'priority': priority,
                    'days_to_stockout': days_left,
                    'predicted_stockout_date': prediction['stockout_date'],
                    'daily_demand': prediction['daily_demand'],
                    'current_stock': current_stock,
                    'confidence': prediction['confidence'],
                    'message': f"Product will run out in {days_left:.1f} days"
                })

        return sorted(alerts, key=lambda x: x['days_to_stockout'] if x['days_to_stockout'] else float('inf'))

    def analyze_all_products(self):
        """Analyze all products in the dataset"""
        analysis_results = {}

        for _, product in self.products_df.iterrows():
            product_id = product['id']
            prediction = self.predict_stockout_date(product_id)
            trend = self.predict_demand_trend(product_id)

            analysis_results[product_id] = {
                'product_name': product['name'],
                'sku': product['sku'],
                'current_stock': product['current_stock'],
                'minimum_stock': product['minimum_stock'],
                'prediction': prediction,
                'trend_analysis': trend
            }

        return analysis_results

    def plot_product_analysis(self, product_id):
        """Plot sales history and prediction for a product"""
        product_data = self.df[self.df['product_id'] == product_id].copy()

        if len(product_data) == 0:
            print(f"No data found for product {product_id}")
            return

        # Daily sales aggregation
        daily_sales = product_data.groupby('sale_date')['quantity_sold'].sum().reset_index()

        plt.figure(figsize=(12, 6))

        # Plot historical sales
        plt.subplot(1, 2, 1)
        plt.plot(daily_sales['sale_date'], daily_sales['quantity_sold'], 'b-', label='Daily Sales')
        plt.title(f'Sales History - Product {product_id}')
        plt.xlabel('Date')
        plt.ylabel('Quantity Sold')
        plt.xticks(rotation=45)
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Plot demand trend if available
        plt.subplot(1, 2, 2)
        if len(daily_sales) >= 3:
            days_since_start = (daily_sales['sale_date'] - daily_sales['sale_date'].min()).dt.days
            plt.scatter(days_since_start, daily_sales['quantity_sold'], alpha=0.6, label='Actual Sales')

            # Fit and plot trend line
            z = np.polyfit(days_since_start, daily_sales['quantity_sold'], 1)
            p = np.poly1d(z)
            plt.plot(days_since_start, p(days_since_start), "r--", alpha=0.8, label='Trend Line')

            plt.title(f'Demand Trend - Product {product_id}')
            plt.xlabel('Days Since First Sale')
            plt.ylabel('Daily Sales')
            plt.legend()
            plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.show()

    def save_demand_forecasts(self, output_file='data/updated_demand_forecasts.csv'):
        """Calculate and save demand forecasts for all products"""
        forecasts = []

        for _, product in self.products_df.iterrows():
            product_id = product['id']
            prediction = self.predict_stockout_date(product_id)

            if prediction['days_to_stockout'] is not None:
                forecast = {
                    'id': f'forecast_{product_id}',
                    'product_id': product_id,
                    'days_to_stockout': prediction['days_to_stockout'],
                    'average_daily_demand': prediction['daily_demand'],
                    'confidence_level': 0.8 if prediction['confidence'] == 'HIGH' else 0.6 if prediction['confidence'] == 'MEDIUM' else 0.4,
                    'historical_data': f'{{"sales_count": {len(self.df[self.df["product_id"] == product_id])}, "period_days": 60}}',
                    'calculation_date': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'created_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                }
                forecasts.append(forecast)

        # Save to CSV
        forecasts_df = pd.DataFrame(forecasts)
        forecasts_df.to_csv(output_file, index=False)
        print(f"Saved {len(forecasts)} demand forecasts to {output_file}")

        return forecasts_df

def main():
    """Example usage of the StockPredictionDB class"""
    predictor = StockPredictionDB()

    # Load data from normalized CSV files
    if not predictor.load_data('data/'):
        print("Failed to load data. Please ensure all CSV files exist in the data/ folder.")
        return

    print("EstokIA Stock Prediction Analysis (Database Format)")
    print("=" * 60)

    # Analyze all products
    results = predictor.analyze_all_products()

    # Display results
    for product_id, analysis in results.items():
        print(f"\nProduct: {analysis['product_name']} (ID: {product_id})")
        print(f"SKU: {analysis['sku']}")
        print(f"Current Stock: {analysis['current_stock']}")
        print(f"Minimum Stock: {analysis['minimum_stock']}")

        prediction = analysis['prediction']
        if prediction['days_to_stockout']:
            print(f"Days to Stockout: {prediction['days_to_stockout']}")
            print(f"Predicted Stockout Date: {prediction['stockout_date']}")
            print(f"Daily Demand: {prediction['daily_demand']}")
            print(f"Confidence: {prediction['confidence']}")
        else:
            print("No stockout prediction available")

        if analysis['trend_analysis']:
            trend = analysis['trend_analysis']
            trend_direction = "increasing" if trend['trend_slope'] > 0 else "decreasing"
            print(f"Demand Trend: {trend_direction} (slope: {trend['trend_slope']:.3f})")
            print(f"Model Accuracy (R²): {trend['r2_score']:.3f}")

    # Generate alerts for critical products
    alerts = predictor.generate_alerts()

    print("\n" + "=" * 60)
    print("STOCK ALERTS")
    print("=" * 60)

    for alert in alerts[:5]:  # Show top 5 critical alerts
        print(f"🚨 {alert['priority']} - Product {alert['product_id']}")
        print(f"   {alert['message']}")
        print(f"   Confidence: {alert['confidence']}")
        print()

    # Save updated demand forecasts
    predictor.save_demand_forecasts()

if __name__ == "__main__":
    main()