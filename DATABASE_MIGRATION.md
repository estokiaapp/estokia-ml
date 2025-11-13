# Database Migration Guide

This document explains how the original CSV data structure was adapted to match the Prisma database schema.

## Original vs New Structure

### Original Structure (estokia_sales_data.csv)
```
product_id,product_name,sku,category,sale_date,quantity_sold,unit_price,current_stock,minimum_stock,supplier
```

### New Database-Compatible Structure

The data has been normalized into separate tables following the Prisma schema:

## Table Mappings

### 1. Users (`users.csv`)
- **Purpose**: System users who can operate the inventory system
- **Columns**: id, name, email, password, type, created_at, updated_at, active
- **Sample Data**: 3 users (1 admin, 2 operators)

### 2. Categories (`categories.csv`)
- **Purpose**: Product categories
- **Mapping**: `category` field from original → normalized category records
- **Columns**: id, name, description, created_at, updated_at
- **Categories Created**:
  - cat_electronics (Eletrônicos)
  - cat_peripherals (Periféricos)
  - cat_monitors (Monitores)
  - cat_storage (Armazenamento)
  - cat_cables (Cabos)
  - cat_components (Componentes)
  - cat_audio (Áudio)

### 3. Suppliers (`suppliers.csv`)
- **Purpose**: Product suppliers
- **Mapping**: `supplier` field from original → normalized supplier records
- **Columns**: id, name, tax_id, email, phone, address, created_at, updated_at, active
- **Suppliers Created**: Acer Brasil, Logitech, Corsair, LG Electronics, Samsung, Premium Cables, NVIDIA, JBL

### 4. Products (`products.csv`)
- **Purpose**: Product catalog with inventory information
- **Mapping**: Direct mapping from original data with foreign key relationships
- **Columns**: id, name, sku, category_id, supplier_id, cost_price, selling_price, current_stock, minimum_stock, maximum_stock, unit_of_measure, description, created_at, updated_at, active
- **Key Changes**:
  - Added cost_price (80% of selling_price)
  - Added maximum_stock and unit_of_measure fields
  - References categories and suppliers by ID

### 5. Sales (`sales.csv`)
- **Purpose**: Sales transaction headers
- **Mapping**: Grouped original sales by date to create sales records
- **Columns**: id, sale_number, user_id, total_amount, status, sale_date, created_at, updated_at
- **Logic**: Each unique sale_date from original data becomes a sale record

### 6. Sale Items (`sale_items.csv`)
- **Purpose**: Individual items within sales transactions
- **Mapping**: Each row from original data becomes a sale item
- **Columns**: id, sale_id, product_id, quantity, unit_price, subtotal, created_at
- **Generated**: 139 sale items from original data

### 7. Stock Movements (`stock_movements.csv`)
- **Purpose**: Track all stock changes (in/out/adjustments)
- **Columns**: id, product_id, user_id, type, quantity, unit_price, reason, notes, movement_date, created_at
- **Sample Data**: Initial stock entries and sample sales movements

### 8. Demand Forecasts (`demand_forecasts.csv`)
- **Purpose**: Store ML prediction results
- **Columns**: id, product_id, days_to_stockout, average_daily_demand, confidence_level, historical_data, calculation_date, created_at
- **Usage**: Output from ML predictions

### 9. Alerts (`alerts.csv`)
- **Purpose**: System alerts for inventory management
- **Columns**: id, product_id, user_id, type, title, message, priority, read, alert_date, created_at
- **Types**: LOW_STOCK, PREDICTED_STOCKOUT, STAGNANT_PRODUCT

### 10. System Settings (`system_settings.csv`)
- **Purpose**: Configurable system parameters
- **Columns**: id, setting_key, setting_value, description, type, created_at, updated_at

## Updated Code

### New File: `stock_prediction_db.py`
- Updated version of the stock prediction system
- Works with normalized database structure
- Includes methods to load and join data from multiple tables
- Maintains compatibility with original analysis functions
- Adds functionality to save demand forecasts back to database format

### Key Changes in Code:
1. **Data Loading**: Now loads multiple CSV files and joins them
2. **Data Structure**: Creates a combined dataset similar to original for analysis
3. **Database Integration**: Ready for Prisma database connection
4. **Enhanced Features**:
   - Save demand forecasts to database format
   - Work with product IDs instead of legacy format
   - Support for all database relationships

## Usage

### Running Analysis with New Structure:
```bash
python stock_prediction_db.py
```

### Loading Data:
```python
predictor = StockPredictionDB()
predictor.load_data('data/')  # Loads all normalized CSV files
```

### Benefits of New Structure:
1. **Normalized Data**: Eliminates redundancy
2. **Referential Integrity**: Proper relationships between entities
3. **Scalability**: Easier to add new features
4. **Database Ready**: Direct mapping to Prisma schema
5. **Audit Trail**: Proper timestamps and user tracking
6. **Extensibility**: Easy to add new product attributes, categories, etc.

## Migration Notes

- All original analysis capabilities are preserved
- Product IDs use the same format (PROD001, PROD002, etc.)
- Current stock levels are maintained in the products table
- Sales data is split between sales (headers) and sale_items (details)
- Ready for database integration with minimal code changes