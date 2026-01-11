#!/usr/bin/env python3
"""
plan.py - Generate a move plan from scan results.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any


def generate_plan(scan_data: Dict[str, Any], target_base: Path) -> Dict[str, Any]:
    """
    Generate a move plan from scan results.

    Args:
        scan_data: Output from scan.py
        target_base: Base directory for organized files

    Returns:
        Move plan dictionary
    """
    plan = {
        "created_at": datetime.now().isoformat(),
        "source_directory": scan_data["directory"],
        "target_base": str(target_base.absolute()),
        "operations": [],
        "stats": {
            "total_moves": 0,
            "by_category": {},
        },
    }

    files = scan_data.get("files", {})

    for category, file_list in files.items():
        if not file_list:
            continue

        target_dir = target_base / category
        plan["stats"]["by_category"][category] = len(file_list)

        for file_info in file_list:
            source = Path(file_info["path"])
            target = target_dir / file_info["name"]

            # Handle name conflicts
            counter = 1
            original_target = target
            while target.exists():
                stem = original_target.stem
                suffix = original_target.suffix
                target = target_dir / f"{stem}_{counter}{suffix}"
                counter += 1

            operation = {
                "action": "move",
                "source": str(source),
                "target": str(target),
                "category": category,
                "size": file_info["size"],
            }

            if "sha256" in file_info:
                operation["sha256"] = file_info["sha256"]

            plan["operations"].append(operation)
            plan["stats"]["total_moves"] += 1

    return plan


def main():
    parser = argparse.ArgumentParser(description="Generate move plan from scan results.")
    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Input scan JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output plan JSON file (default: stdout)"
    )
    parser.add_argument(
        "-t", "--target",
        type=Path,
        default=Path.home() / "Downloads" / "Organized",
        help="Target base directory for organized files"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output"
    )

    args = parser.parse_args()

    try:
        if not args.input.exists():
            raise FileNotFoundError(f"Input file not found: {args.input}")

        scan_data = json.loads(args.input.read_text())

        if not args.quiet:
            print(f"Generating plan from {args.input}...", file=sys.stderr)

        plan = generate_plan(scan_data, args.target)

        if not args.quiet:
            print(f"Plan: {plan['stats']['total_moves']} files to move", file=sys.stderr)
            for cat, count in plan["stats"]["by_category"].items():
                print(f"  {cat}: {count} files", file=sys.stderr)

        json_output = json.dumps(plan, indent=2, ensure_ascii=False)

        if args.output:
            args.output.write_text(json_output)
            if not args.quiet:
                print(f"Plan saved to {args.output}", file=sys.stderr)
        else:
            print(json_output)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
