#!/usr/bin/env python3
"""Retired legacy example; never silently bypass the current human gates."""
import sys
print('Legacy fixture retired. Use examples/full-workflow/run.py --output-dir NEW_EMPTY_DIR --initialize-composition; it explicitly simulates both approvals for the known synthetic source only.',file=sys.stderr)
raise SystemExit(2)
