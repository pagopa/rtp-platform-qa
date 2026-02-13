#!/usr/bin/env bash

set -eo pipefail

show_help() {
  cat << EOF
Script to run performance tests with k6 on Azure Container Apps

USAGE:
  ./run-tests.sh <test-folder> <test-script.js> <output-format> [scenario]
  ./run-tests.sh <path/to/script.js> <output-format> [scenario]
  ./run-tests.sh --help

PARAMETERS:
  <test-folder>        Folder containing k6 scripts (e.g., tests/rtp-activator)
  <test-script.js>     Script filename within folder (e.g., activation-finder.js)
  <path/to/script.js>  Or full relative path to script file (e.g., tests/rtp-activator/activation.js)
  <output-format>      Desired output format (required):
                       - console:     Terminal output (default)
                       - dashboard:   Interactive web dashboard at http://127.0.0.1:5665
                       - json:        Detailed JSON results file
                       - prometheus:  Send metrics to Prometheus server

  [scenario]           Test scenario to run (optional):
                       - stress_test: Gradual load test (default)
                       - soak_test:   Long-term endurance test
                       - spike_test:  Test with sudden load spikes


  OUTPUT FORMATS:
    console   | Terminal output (default)
    dashboard | Interactive web dashboard at http://127.0.0.1:5665
    json      | Detailed JSON results file
    prometheus| Send metrics to Prometheus server

EXAMPLES:
  # Run stress test for activation.js using script path with console output
  ./run-tests.sh rtp-activator/activation.js console

  # Run spike test with web dashboard using direct script path
  ./run-tests.sh rtp-activator/activation.js dashboard spike_test

  # Run stress test for activation-finder.js in rtp-activator folder
  ./run-tests.sh tests/rtp-activator activation-finder.js

  # Generate JSON for soak test of activation-finder.js
  ./run-tests.sh tests/rtp-activator activation-finder.js json soak_test

ENVIRONMENT:
  The ../.env file is loaded if present.
  For Prometheus output: define PROM_HOST and PROM_PORT.

NOTES:
  For tests on Azure Container Apps, monitor Azure metrics
  during execution to verify scaling and performance.
EOF
  exit 0
}

if [ "$#" -eq 0 ] || [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
  show_help
fi

if [ -f ../.env ]; then
  set -a
  source ../.env
  set +a
fi

INPUT="$1"; shift
if [[ "$INPUT" == *.js ]]; then
  if [ -f "$INPUT" ]; then
    SCRIPT="$INPUT"
  elif [ -f "tests/$INPUT" ]; then
    SCRIPT="tests/$INPUT"
  else
    echo "Error: Script '$INPUT' not found"; exit 1
  fi
else
  DIR="$INPUT"
  if [ ! -d "$DIR" ] && [ -d "tests/$DIR" ]; then
    DIR="tests/$DIR"
  fi
  if [ ! -d "$DIR" ]; then
    echo "Error: Directory '$INPUT' not found"; exit 1
  fi
  FILE="$1"; shift
  if [ -z "$FILE" ]; then
    echo "Error: Please specify a script filename within '$DIR'"; exit 1
  fi
  SCRIPT="$DIR/$FILE"
  if [ ! -f "$SCRIPT" ]; then
    echo "Error: Script '$SCRIPT' not found in '$DIR'"; exit 1
  fi
fi
if [ -z "$1" ]; then
  echo "Error: Please specify an output format"
  exit 1
fi
FORMAT="$1"; shift

SCENARIO="${1:-stress_test}"
export SCENARIO
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
echo "Running performance test: $SCRIPT with output format: $FORMAT (Scenario: $SCENARIO)"


case "$FORMAT" in
  "dashboard" | "web-dashboard" | "web_dashboard")
    echo "Starting k6 with web dashboard..."
    k6 run --out web-dashboard "$SCRIPT" &
    sleep 2
    open http://127.0.0.1:5665
    wait
    ;;

  "json")
    RESULT_FILE="results_${SCENARIO}_${TIMESTAMP}.json"
    echo "Saving JSON output to $RESULT_FILE"
    k6 run --out json="$RESULT_FILE" "$SCRIPT"
    echo "JSON created: $RESULT_FILE"
    ;;

  "prometheus")
    if [ -z "$PROM_HOST" ] || [ -z "$PROM_PORT" ]; then
      echo "ERROR: PROM_HOST and PROM_PORT must be defined in .env"
      exit 1
    fi
    echo "Sending metrics to Prometheus: $PROM_HOST:$PROM_PORT"
    k6 run --out prometheus-remotely="$PROM_HOST:$PROM_PORT" "$SCRIPT"
    ;;

  *)
    echo "Running with console output"
    k6 run "$SCRIPT"
    ;;
esac

exit 0
