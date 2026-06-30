#!/usr/bin/env python3
"""
Remove Allure report run directories beyond the last N runs from gh-pages.

Keeps the N most recent numbered directories (by run number) and deletes
the rest, including corresponding subdirectories (functional/, bdd/, ux/, contract/, aggregate/).

Usage:
    python cleanup-old-reports.py [keep=20] [gh-pages-path=.]
"""
import shutil
import sys
from pathlib import Path

REPORT_SUBDIRS = ['functional', 'bdd', 'ux', 'contract', 'aggregate']

try:
    keep = int(sys.argv[1]) if len(sys.argv) > 1 else 20
except ValueError:
    print(f"Invalid keep value: {sys.argv[1]!r} (expected non-negative integer)", file=sys.stderr)
    sys.exit(2)
if keep < 0:
    print(f"Invalid keep value: {keep} (expected non-negative integer)", file=sys.stderr)
    sys.exit(2)
gh_pages = Path(sys.argv[2]) if len(sys.argv) > 2 else Path('.')

run_dirs = sorted(
    [d for d in gh_pages.iterdir() if d.is_dir() and d.name.isdigit()],
    key=lambda d: int(d.name),
    reverse=True,
)

to_delete = run_dirs[keep:]

if not to_delete:
    print(f'Nothing to delete ({len(run_dirs)} run(s) found, keeping up to {keep})')
    sys.exit(0)

for run_dir in to_delete:
    print(f'Removing run {run_dir.name}...')
    shutil.rmtree(run_dir)
    for sub in REPORT_SUBDIRS:
        sub_run = gh_pages / sub / run_dir.name
        if sub_run.is_dir():
            shutil.rmtree(sub_run)
            print(f'  Removed {sub}/{run_dir.name}')
        elif sub_run.exists():
            sub_run.unlink()
            print(f'  Removed {sub}/{run_dir.name}')

print(f'\nDone: removed {len(to_delete)} run(s), kept {min(len(run_dirs), keep)}')
