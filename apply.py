#!/usr/bin/env python3
"""
apply.py - Execute the move plan, creating category directories and moving files.
"""

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA256 hash of a file."""
    hash_obj = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except (IOError, PermissionError) as e:
        return f"ERROR:{e}"


def apply_plan(
    plan: Dict[str, Any],
    dry_run: bool = False,
    verify_hash: bool = False,
    quiet: bool = False
) -> Dict[str, Any]:
    """
    Execute the move plan.

    Args:
        plan: Move plan from plan.py
        dry_run: If True, only simulate moves
        verify_hash: Verify file integrity after move
        quiet: Suppress progress output

    Returns:
        Execution log
    """
    log = {
        "executed_at": datetime.now().isoformat(),
        "dry_run": dry_run,
        "plan_source": plan.get("created_at", "unknown"),
        "operations": [],
        "stats": {
            "success": 0,
            "failed": 0,
            "skipped": 0,
        },
    }

    target_base = Path(plan["target_base"])

    # Create category directories
    categories = set(op["category"] for op in plan["operations"])
    for category in categories:
        cat_dir = target_base / category
        if dry_run:
            if not quiet:
                print(f"[DRY RUN] Would create directory: {cat_dir}", file=sys.stderr)
        else:
            cat_dir.mkdir(parents=True, exist_ok=True)

    # Execute move operations
    for op in plan["operations"]:
        source = Path(op["source"])
        target = Path(op["target"])

        result = {
            "source": op["source"],
            "target": op["target"],
            "category": op["category"],
            "status": "pending",
        }

        # Check if source exists
        if not source.exists():
            result["status"] = "skipped"
            result["reason"] = "source not found"
            log["operations"].append(result)
            log["stats"]["skipped"] += 1
            if not quiet:
                print(f"[SKIP] {source.name}: source not found", file=sys.stderr)
            continue

        # Check if target already exists
        if target.exists():
            result["status"] = "skipped"
            result["reason"] = "target exists"
            log["operations"].append(result)
            log["stats"]["skipped"] += 1
            if not quiet:
                print(f"[SKIP] {source.name}: target exists", file=sys.stderr)
            continue

        try:
            if dry_run:
                result["status"] = "dry_run"
                if not quiet:
                    print(f"[DRY RUN] {source.name} -> {op['category']}/", file=sys.stderr)
            else:
                # Ensure parent directory exists
                target.parent.mkdir(parents=True, exist_ok=True)

                # Move the file
                shutil.move(str(source), str(target))
                result["status"] = "success"

                # Verify hash if requested
                if verify_hash and "sha256" in op:
                    new_hash = compute_file_hash(target)
                    if new_hash == op["sha256"]:
                        result["hash_verified"] = True
                    else:
                        result["hash_verified"] = False
                        result["warning"] = "Hash mismatch after move"

                if not quiet:
                    print(f"[MOVED] {source.name} -> {op['category']}/", file=sys.stderr)

            log["stats"]["success"] += 1

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            log["stats"]["failed"] += 1
            if not quiet:
                print(f"[FAIL] {source.name}: {e}", file=sys.stderr)

        log["operations"].append(result)

    return log


def main():
    parser = argparse.ArgumentParser(description="Execute move plan to organize files.")
    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Input plan JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output log JSON file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate moves without actually moving files"
    )
    parser.add_argument(
        "--verify-hash",
        action="store_true",
        help="Verify file integrity after move"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output"
    )

    args = parser.parse_args()

    try:
        if not args.input.exists():
            raise FileNotFoundError(f"Plan file not found: {args.input}")

        plan = json.loads(args.input.read_text())

        if not args.quiet:
            mode = "[DRY RUN] " if args.dry_run else ""
            print(f"{mode}Applying plan with {plan['stats']['total_moves']} operations...", file=sys.stderr)

        log = apply_plan(
            plan,
            dry_run=args.dry_run,
            verify_hash=args.verify_hash,
            quiet=args.quiet
        )

        if not args.quiet:
            print(f"\nResults: {log['stats']['success']} success, "
                  f"{log['stats']['failed']} failed, "
                  f"{log['stats']['skipped']} skipped", file=sys.stderr)

        json_output = json.dumps(log, indent=2, ensure_ascii=False)

        if args.output:
            args.output.write_text(json_output)
            if not args.quiet:
                print(f"Log saved to {args.output}", file=sys.stderr)
        else:
            print(json_output)

        return 0 if log["stats"]["failed"] == 0 else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
