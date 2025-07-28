#!/usr/bin/env bash
set -a
source ../.env
set +a

if [ -z "$1" ]; then
  echo "Usage: $0 <test-script.js> [output-format]"
  echo "Output formats: web-dashboard, json, console (default)"
  exit 1
fi

SCRIPT=$1
OUTPUT_FORMAT=${2:-"console"}

echo "Running performance test: $SCRIPT with output format: $OUTPUT_FORMAT"

case "$OUTPUT_FORMAT" in
  "dashboard" | "web-dashboard")
    echo "Starting k6 with web dashboard..."
    k6 run --out web-dashboard "$SCRIPT" &
    sleep 5
    open http://127.0.0.1:5665
    wait
    ;;
  "json")
    TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
    RESULT_FILE="results_${TIMESTAMP}.json"
    echo "Saving results to $RESULT_FILE..."
    k6 run --out json="$RESULT_FILE" "$SCRIPT"
    echo "Test complete! Results saved to $RESULT_FILE"
    ;;
  *)
    k6 run "$SCRIPT"
    ;;
esac