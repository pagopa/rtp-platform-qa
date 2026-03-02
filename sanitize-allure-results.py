#!/usr/bin/env python3
"""
Script to sanitize bearer tokens and JWT patterns from Allure JSON results.
This is run as a post-processing step before publishing reports to gh-pages.
"""
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict


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

    # Pattern 1: Bearer tokens (any length >= 20 chars)
    text = re.sub(
        r'Bearer\s+[A-Za-z0-9_\-\.]{20,}',
        'Bearer ***REDACTED***',
        text
    )

    # Pattern 2: JWT tokens (header.payload.signature format)
    # Matches eyJ... (base64 header) followed by .eyJ... (base64 payload)
    text = re.sub(
        r'eyJ[A-Za-z0-9_\-]{10,}\.eyJ[A-Za-z0-9_\-\.]{10,}',
        '***REDACTED_JWT***',
        text
    )

    # Pattern 3: Standalone eyJ... patterns (JWT fragments)
    text = re.sub(
        r'\beyJ[A-Za-z0-9_\-\.]{20,}',
        '***REDACTED_JWT***',
        text
    )

    # Pattern 4: Authorization header values
    text = re.sub(
        r'(Authorization["\']?\s*:\s*["\']?)([A-Za-z0-9_\-\.]{30,})',
        r'\1***REDACTED***',
        text
    )

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
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        sanitized_data = sanitize_dict(data)

        # Check if anything was modified
        original_json = json.dumps(data, sort_keys=True)
        sanitized_json = json.dumps(sanitized_data, sort_keys=True)

        if original_json != sanitized_json:
            with open(file_path, 'w', encoding='utf-8') as f:
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
    if len(sys.argv) > 1:
        allure_results_dir = Path(sys.argv[1])
    else:
        allure_results_dir = Path('allure-results')

    if not allure_results_dir.exists():
        print(f"❌ Error: Directory {allure_results_dir} does not exist")
        sys.exit(1)

    print(f"🔍 Scanning {allure_results_dir} for JSON files...")

    json_files = list(allure_results_dir.rglob('*.json'))

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


if __name__ == '__main__':
    main()
