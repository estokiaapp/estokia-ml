#!/usr/bin/env python3
"""
Daily Prediction Scheduler
Runs sales predictions for all active users automatically

Usage:
  - Add to crontab: 0 2 * * * /path/to/venv/bin/python3 run_daily_predictions.py
  - Or run manually: python3 run_daily_predictions.py
"""

import sqlite3
import subprocess
import sys
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('predictions.log'),
        logging.StreamHandler()
    ]
)

# Paths
DB_PATH = '/Users/gkanawati/Documents/GitHub/estokia/estokia-backend/prisma/dev.db'
SCRIPT_DIR = Path(__file__).parent
VENV_PYTHON = SCRIPT_DIR / 'venv' / 'bin' / 'python3'
PREDICTION_SCRIPT = SCRIPT_DIR / 'sales_prediction.py'


def get_active_users():
    """Fetch all active users from the database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, email
            FROM users
            WHERE active = 1
            ORDER BY id
        """)
        users = cursor.fetchall()
        conn.close()
        return users
    except Exception as e:
        logging.error(f"Failed to fetch users: {e}")
        return []


def run_prediction_for_user(user_id, user_name):
    """Run sales prediction for a specific user"""
    try:
        logging.info(f"Starting prediction for user {user_id} ({user_name})")

        result = subprocess.run(
            [str(VENV_PYTHON), str(PREDICTION_SCRIPT), str(user_id)],
            cwd=str(SCRIPT_DIR),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0:
            logging.info(f"✓ Successfully completed predictions for user {user_id}")
            return True
        else:
            logging.error(f"✗ Prediction failed for user {user_id}")
            logging.error(f"Error output: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        logging.error(f"✗ Prediction timeout for user {user_id}")
        return False
    except Exception as e:
        logging.error(f"✗ Exception for user {user_id}: {e}")
        return False


def main():
    """Main execution routine"""
    start_time = datetime.now()
    logging.info("=" * 80)
    logging.info("Starting Daily Prediction Routine")
    logging.info("=" * 80)

    # Get all active users
    users = get_active_users()

    if not users:
        logging.warning("No active users found")
        return

    logging.info(f"Found {len(users)} active users")

    # Run predictions for each user
    success_count = 0
    failed_count = 0

    for user_id, user_name, user_email in users:
        if run_prediction_for_user(user_id, user_name):
            success_count += 1
        else:
            failed_count += 1

    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    logging.info("=" * 80)
    logging.info("Prediction Routine Summary")
    logging.info("=" * 80)
    logging.info(f"Total users: {len(users)}")
    logging.info(f"Successful: {success_count}")
    logging.info(f"Failed: {failed_count}")
    logging.info(f"Duration: {duration:.2f} seconds")
    logging.info("=" * 80)

    # Exit with error code if any failed
    if failed_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
