-- Migration: Add user_id to demand_forecasts table
-- Date: 2025-11-12
-- Purpose: Enable per-user demand forecasting

-- Step 1: Add user_id column (nullable initially for backward compatibility)
ALTER TABLE demand_forecasts
ADD COLUMN user_id INTEGER;

-- Step 2: Create index on user_id for query performance
CREATE INDEX demand_forecasts_user_id_idx ON demand_forecasts(user_id);

-- Step 3: Add composite index for user + product queries
CREATE INDEX demand_forecasts_user_product_idx ON demand_forecasts(user_id, product_id);

-- Note: SQLite doesn't support adding foreign key constraints to existing tables
-- The foreign key will be validated at the application level
-- To fully enforce, you would need to recreate the table with the constraint
