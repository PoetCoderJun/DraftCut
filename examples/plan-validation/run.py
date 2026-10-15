#!/usr/bin/env python3
"""Offline illustration of the existing plan gate; no media or model calls."""
import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("motiontalk_validate_plan", ROOT / "scripts/validate_plan.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
plan = json.loads((Path(__file__).parent / "plan.json").read_text())
assert validator.validate(plan) == [], "synthetic valid plan failed"
print("PASS: synthetic plan structure; no human approval implied")
draft = copy.deepcopy(plan)
draft.pop("workflow")
assert any("migration" in error for error in validator.validate(draft))
print("REJECT: legacy boolean approval without new workflow")
gapped = copy.deepcopy(plan)
gapped["cues"][1]["start_seconds"] = 1.1
assert any("cue gap or overlap" in error for error in validator.validate(gapped))
print("REJECT: timeline gap")
