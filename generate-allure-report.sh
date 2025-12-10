#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$ROOT_DIR/allure-results"
REPORT_DIR="$ROOT_DIR/allure-report"

echo "[INFO] Cleaning previous Allure data..."
rm -rf "$RESULTS_DIR" "$REPORT_DIR"
mkdir -p "$RESULTS_DIR"

echo "[INFO] Running test suites..."

echo "[1/4] Functional tests (pytest)..."
pytest functional-tests/tests -q --alluredir="$RESULTS_DIR"

echo "[2/4] BDD tests (behave)..."
behave bdd-tests \
  --format allure_behave.formatter:AllureFormatter \
  --outfile "$RESULTS_DIR"

echo "[3/4] UX tests (pytest + Playwright)..."
pytest ux-tests/tests -q --alluredir="$RESULTS_DIR"

echo "[4/4] Contract tests (pytest)..."
pytest contract-tests -q --alluredir="$RESULTS_DIR"

echo "[INFO] All tests finished."

if ! command -v allure >/dev/null 2>&1; then
  echo "[ERROR] 'allure' CLI not found. Install it first, e.g.:"
  echo "  brew install allure"
  exit 1
fi

echo "[INFO] Generating Allure HTML report..."
allure generate "$RESULTS_DIR" -o "$REPORT_DIR" --clean

echo "[INFO] Opening Allure report on localhost..."
allure open "$REPORT_DIR"
