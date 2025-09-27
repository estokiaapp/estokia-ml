import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class StockPrediction:
    def __init__(self):
        self.model = LinearRegression()
        self.predictions = {}

    def load_data(self, csv_path):
        """Load sales and stock data from CSV"""
        try:
            self.df = pd.read_csv(csv_path)
            self.df['sale_date'] = pd.to_datetime(self.df['sale_date'])
            return True
        except Exception as e:
            print(f"Error loading data: {e}")
            return False

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

    def predict_stockout_date(self, product_id, current_stock):
        """Predict when a product will run out of stock"""
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

    def generate_alerts(self, products_stock):
        """Generate stock alerts for products"""
        alerts = []

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
        unique_products = self.df['product_id'].unique()
        analysis_results = {}

        for product_id in unique_products:
            # Get latest stock from the data (you might want to fetch this from your DB)
            latest_entry = self.df[self.df['product_id'] == product_id].iloc[-1]
            current_stock = latest_entry.get('current_stock', 100)  # Default if not in CSV

            prediction = self.predict_stockout_date(product_id, current_stock)
            trend = self.predict_demand_trend(product_id)

            analysis_results[product_id] = {
                'product_name': latest_entry.get('product_name', f'Product {product_id}'),
                'current_stock': current_stock,
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

def main():
    """Example usage of the StockPrediction class"""
    predictor = StockPrediction()

    # Load data
    if not predictor.load_data('data/estokia_sales_data.csv'):
        print("Failed to load data. Please ensure the CSV file exists.")
        return

    print("EstokIA Stock Prediction Analysis")
    print("=" * 50)

    # Analyze all products
    results = predictor.analyze_all_products()

    # Display results
    for product_id, analysis in results.items():
        print(f"\nProduct: {analysis['product_name']} (ID: {product_id})")
        print(f"Current Stock: {analysis['current_stock']}")

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
    products_stock = {pid: analysis['current_stock'] for pid, analysis in results.items()}
    alerts = predictor.generate_alerts(products_stock)

    print("\n" + "=" * 50)
    print("STOCK ALERTS")
    print("=" * 50)

    for alert in alerts[:5]:  # Show top 5 critical alerts
        print(f"🚨 {alert['priority']} - Product {alert['product_id']}")
        print(f"   {alert['message']}")
        print(f"   Confidence: {alert['confidence']}")
        print()

if __name__ == "__main__":
    main()