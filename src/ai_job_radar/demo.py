"""Command-line entry point for the local synthetic evidence demo."""

from __future__ import annotations

import argparse
import json
import sys

from .requirement_evidence import ValidationError, evaluate_assessment, load_assessment, serialize_result


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a synthetic requirement/evidence assessment.")
    parser.add_argument("--assessment", required=True, help="Path to a synthetic assessment JSON file.")
    args = parser.parse_args()
    try:
        result = evaluate_assessment(load_assessment(args.assessment))
    except ValidationError as error:
        sys.stderr.write(json.dumps({"error": "VALIDATION_ERROR", "message": str(error)}, sort_keys=True, indent=2) + "\n")
        return 2
    sys.stdout.write(serialize_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
