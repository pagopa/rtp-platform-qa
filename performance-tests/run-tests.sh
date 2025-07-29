#!/usr/bin/env bash

set -eo pipefail

show_help() {
  cat << EOF
Script to run performance tests with k6 on Azure Container Apps

USAGE:
  ./run-tests.sh <test-script.js> <output-format> [scenario]
  ./run-tests.sh --help

PARAMETERS:
  <test-script.js>     k6 script to run (e.g., activation-finder.js)
  <output-format>      Desired output format:
                       - console:     Terminal output (default)
                       - dashboard:   Interactive web dashboard at http://127.0.0.1:5665
                       - json:        Detailed JSON results file
                       - html:        HTML report (requires k6-reporter)
                       - prometheus:  Send metrics to Prometheus server

  [scenario]           Test scenario to run (optional):
                       - stress_test: Gradual load test (default)
                       - soak_test:   Long-term endurance test
                       - spike_test:  Test with sudden load spikes

EXAMPLES:
  # Run stress test with console output
  ./run-tests.sh activation-finder.js console

  # Run spike test with web dashboard
  ./run-tests.sh activation-finder.js dashboard spike_test

  # Generate HTML report for soak test
  ./run-tests.sh activation-finder.js html soak_test

ENVIRONMENT:
  The ../.env file is loaded if present.
  For Prometheus output: define PROM_HOST and PROM_PORT.

NOTES:
  For tests on Azure Container Apps, monitor Azure metrics
  during execution to verify scaling and performance.
EOF
  exit 0
}

if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
  show_help
fi

if [ -f ../.env ]; then
  set -a
  source ../.env
  set +a
fi

if [ -z "$1" ]; then
  echo "Usage: $0 <test-script.js> <output-format> [scenario]"
  echo "Formats: console, dashboard, json, html, prometheus"
  echo "Scenarios: stress_test, soak_test, spike_test"
  echo "Run '$0 --help' for more information"
  exit 1
fi

SCRIPT="$1"
FORMAT="${2:-console}"
SCENARIO="${3:-stress_test}"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo "Running performance test: $SCRIPT with output format: $FORMAT (Scenario: $SCENARIO)"

SCENARIO_OPT=""
if [ "$SCENARIO" != "stress_test" ]; then
  SCENARIO_OPT="--scenario $SCENARIO"
fi

case "$FORMAT" in
  "dashboard" | "web-dashboard")
    echo "Starting k6 with web dashboard..."
    k6 run --out web-dashboard $SCENARIO_OPT "$SCRIPT" &
    sleep 2
    open http://127.0.0.1:5665
    wait
    ;;

  "json")
    RESULT_FILE="results_${SCENARIO}_${TIMESTAMP}.json"
    echo "Saving JSON output to $RESULT_FILE"
    k6 run --out json="$RESULT_FILE" $SCENARIO_OPT "$SCRIPT"
    echo "JSON created: $RESULT_FILE"
    ;;

  "html")
    JSON_FILE="results_${SCENARIO}_${TIMESTAMP}.json"
    HTML_FILE="report_${SCENARIO}_${TIMESTAMP}.html"
    echo "Generating temporary JSON: $JSON_FILE"
    k6 run --out json="$JSON_FILE" $SCENARIO_OPT "$SCRIPT"
    echo "Converting JSON to HTML: $HTML_FILE"
    if ! command -v k6-reporter >/dev/null; then
      echo "ERROR: k6-reporter not installed. Run: npm install -g k6-reporter"
      exit 1
    fi
    k6-reporter --out html="$HTML_FILE" "$JSON_FILE"
    echo "HTML Report created: $HTML_FILE"
    ;;

  "prometheus")
    if [ -z "$PROM_HOST" ] || [ -z "$PROM_PORT" ]; then
      echo "ERROR: PROM_HOST and PROM_PORT must be defined in .env"
      exit 1
    fi
    echo "Sending metrics to Prometheus: $PROM_HOST:$PROM_PORT"
    k6 run --out prometheus-remotely="$PROM_HOST:$PROM_PORT" $SCENARIO_OPT "$SCRIPT"
    ;;

  *)
    echo "Running with console output"
    k6 run $SCENARIO_OPT "$SCRIPT"
    ;;
esac

exit 0