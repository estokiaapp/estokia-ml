#!/bin/bash
# Setup cron jobs for EstokIA predictions
# Runs at: 02:00 AM, 08:00 AM, and 17:30 PM daily

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_PATH="${SCRIPT_DIR}/venv/bin/python3"
PREDICTION_SCRIPT="${SCRIPT_DIR}/run_daily_predictions.py"
LOG_FILE="${SCRIPT_DIR}/cron.log"

echo "EstokIA Prediction Scheduler Setup"
echo "===================================="
echo ""
echo "Script directory: ${SCRIPT_DIR}"
echo "Python path: ${PYTHON_PATH}"
echo "Prediction script: ${PREDICTION_SCRIPT}"
echo ""

# Check if files exist
if [ ! -f "${PYTHON_PATH}" ]; then
    echo "❌ Error: Python virtual environment not found at ${PYTHON_PATH}"
    echo "   Please run: python3 -m venv venv"
    exit 1
fi

if [ ! -f "${PREDICTION_SCRIPT}" ]; then
    echo "❌ Error: Prediction script not found at ${PREDICTION_SCRIPT}"
    exit 1
fi

# Make scripts executable
chmod +x "${PREDICTION_SCRIPT}"
echo "✓ Made prediction script executable"

# Create cron entries
CRON_ENTRY_1="0 2 * * * ${PYTHON_PATH} ${PREDICTION_SCRIPT} >> ${LOG_FILE} 2>&1"
CRON_ENTRY_2="0 8 * * * ${PYTHON_PATH} ${PREDICTION_SCRIPT} >> ${LOG_FILE} 2>&1"
CRON_ENTRY_3="30 17 * * * ${PYTHON_PATH} ${PREDICTION_SCRIPT} >> ${LOG_FILE} 2>&1"

echo ""
echo "Cron schedule to be added:"
echo "===================================="
echo "02:00 AM - ${CRON_ENTRY_1}"
echo "08:00 AM - ${CRON_ENTRY_2}"
echo "17:30 PM - ${CRON_ENTRY_3}"
echo ""

# Backup existing crontab
crontab -l > /tmp/crontab_backup_$(date +%Y%m%d_%H%M%S).txt 2>/dev/null
echo "✓ Backed up existing crontab to /tmp/"

# Check if entries already exist
EXISTING_CRON=$(crontab -l 2>/dev/null | grep -c "run_daily_predictions.py")

if [ "$EXISTING_CRON" -gt 0 ]; then
    echo ""
    echo "⚠️  Warning: Found $EXISTING_CRON existing prediction cron job(s)"
    echo ""
    read -p "Remove existing entries and add new ones? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove existing entries
        crontab -l 2>/dev/null | grep -v "run_daily_predictions.py" | crontab -
        echo "✓ Removed existing entries"
    else
        echo "❌ Cancelled. No changes made."
        exit 0
    fi
fi

# Add new cron entries
(crontab -l 2>/dev/null; echo "# EstokIA Predictions - Run 3x daily (02:00, 08:00, 17:30)") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_ENTRY_1") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_ENTRY_2") | crontab -
(crontab -l 2>/dev/null; echo "$CRON_ENTRY_3") | crontab -

echo ""
echo "✅ Cron jobs installed successfully!"
echo ""
echo "Current crontab:"
echo "===================================="
crontab -l | grep -A 3 "EstokIA"
echo ""
echo "Schedule Summary:"
echo "  • 02:00 AM - Night processing (fresh morning data)"
echo "  • 08:00 AM - Morning update (start of business)"
echo "  • 17:30 PM - Evening update (end of business)"
echo ""
echo "Logs will be written to: ${LOG_FILE}"
echo "View logs: tail -f ${LOG_FILE}"
echo ""
echo "To remove cron jobs later:"
echo "  crontab -e"
echo "  (delete the EstokIA lines)"
echo ""
