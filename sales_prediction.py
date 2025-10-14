import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

DB_PATH = '/Users/gkanawati/Documents/GitHub/estokia/estokia-backend/prisma/estokia.db'

class SalesPredictionDB:

    def __init__(self, db_path=DB_PATH, user_id=1):
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
        self.products = pd.read_sql('SELECT * FROM products', self.conn)
        self.sales = pd.read_sql(
            'SELECT * FROM sales WHERE user_id=?',
            self.conn,
            params=(self.user_id,)
        )
        self.sale_items = pd.read_sql('SELECT * FROM sale_items', self.conn)

        self.conn.close()

        print(f"Data loaded successfully for user_id={self.user_id}")
        print(f"Products: {len(self.products)}")
        print(f"Sales: {len(self.sales)}")
        print(f"Sale Items: {len(self.sale_items)}")


    def prepare_data(self):
        """Prepare data for sales prediction - unified DataFrame approach"""
        product_sales = self.sale_items
        print('~ prepare_data - product_sales: \n', product_sales)
        print('~ prepare_data - sales: \n', self.sales)

        if product_sales.empty:
            return None

        # Merge sale items with sales to get sale_date
        sales_data = product_sales.merge(
            self.sales[['id', 'sale_date']],
            left_on='sale_id',
            right_on='id',
            how='left'
        )

        sales_data['sale_date'] = pd.to_datetime(sales_data['sale_date']).dt.normalize()

        print('~ prepare_data - Merged sales_data: \n', sales_data)

        # Group by product_id and sale_date, sum quantities
        sales_aggregated = sales_data.groupby(['product_id', 'sale_date']).agg({'quantity': 'sum'}).reset_index()

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
        """Train a sales prediction model for a specific product"""
        # EXEMPLO
        # Criar modelo de regressao linear
        # Variavel independente ?
        X = df.index.values.reshape(-1, 1)
        # Variavel dependente (vendas)
        y = df["quantity"].values
        # Treinar o modelo
        modelo = LinearRegression().fit(X, y)

def main():
    """Example usage of the SalesPredictionDB class"""
    predictor = SalesPredictionDB()
    predictor.load_data()
    predictor.prepare_data()

if __name__ == "__main__":
    main()