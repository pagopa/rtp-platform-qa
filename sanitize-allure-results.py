#!/usr/bin/env python3
"""
Script to sanitize bearer tokens and JWT patterns from Allure JSON results.
This is run as a post-processing step before publishing reports to gh-pages.
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

_MULTI_SEGMENT_TOKEN = r"[\w-]+(?:\.+[\w-]+)+"


def sanitize_text(text: str) -> str:
    """
    Remove sensitive tokens from text.

    Patterns sanitized:
    - Bearer tokens (JWT format)
    - Standalone JWT tokens (eyJ... format)
    - Authorization headers
    """
    if not isinstance(text, str):
        return text

    text = re.sub(r"Bearer\s+" + _MULTI_SEGMENT_TOKEN, "Bearer ***REDACTED***", text)

    text = re.sub(r"eyJ" + _MULTI_SEGMENT_TOKEN, "***REDACTED_JWT***", text)

    text = re.sub(r"\beyJ" + _MULTI_SEGMENT_TOKEN, "***REDACTED_JWT***", text)

    text = re.sub(r'(Authorization["\']?\s*:\s*["\']?)' + _MULTI_SEGMENT_TOKEN, r"\1***REDACTED***", text)

    return text


def sanitize_dict(obj: Any) -> Any:
    """
    Recursively sanitize all string values in a dictionary or list.
    """
    if isinstance(obj, dict):
        return {key: sanitize_dict(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_dict(item) for item in obj]
    elif isinstance(obj, str):
        return sanitize_text(obj)
    else:
        return obj


def sanitize_json_file(file_path: Path) -> bool:
    """
    Sanitize a single JSON file.
    Returns True if file was modified, False otherwise.
    """
    try:
        with open(file_path, encoding="utf-8") as f:
            data = json.load(f)

        sanitized_data = sanitize_dict(data)

        # Check if anything was modified
        original_json = json.dumps(data, sort_keys=True)
        sanitized_json = json.dumps(sanitized_data, sort_keys=True)

        if original_json != sanitized_json:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(sanitized_data, f, ensure_ascii=False, indent=2)
            return True

        return False

    except json.JSONDecodeError as e:
        print(f"⚠️  Warning: Could not parse JSON file {file_path}: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"⚠️  Warning: Error processing {file_path}: {e}", file=sys.stderr)
        return False


def main():
    """
    Main function to sanitize all JSON files in allure-results directory.
    """
    parser = argparse.ArgumentParser(description="Sanitize bearer tokens and JWTs from Allure JSON results.")
    parser.add_argument(
        "results_dir",
        nargs="?",
        default="allure-results",
        help="Path to allure-results directory (default: allure-results)",
    )
    args = parser.parse_args()

    allure_results_dir = Path(args.results_dir)

    if not allure_results_dir.exists():
        print(f"❌ Error: Directory {allure_results_dir} does not exist")
        sys.exit(1)

    print(f"🔍 Scanning {allure_results_dir} for JSON files...")

    json_files = list(allure_results_dir.rglob("*.json"))

    if not json_files:
        print(f"⚠️  No JSON files found in {allure_results_dir}")
        sys.exit(0)

    modified_count = 0
    for json_file in json_files:
        if sanitize_json_file(json_file):
            modified_count += 1
            print(f"✅ Sanitized: {json_file.relative_to(allure_results_dir)}")

    if modified_count > 0:
        print(f"\n✨ Sanitized {modified_count} file(s) out of {len(json_files)} total")
    else:
        print(f"\n✅ All {len(json_files)} file(s) are clean (no tokens found)")


if __name__ == "__main__":
    main()
