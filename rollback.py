#!/usr/bin/env python3
"""
rollback.py - Undo the last apply by reading the move log.
"""

import argparse
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def rollback_operations(
    log: Dict[str, Any],
    dry_run: bool = False,
    quiet: bool = False
) -> Dict[str, Any]:
    """
    Rollback move operations from a log.

    Args:
        log: Execution log from apply.py
        dry_run: If True, only simulate rollback
        quiet: Suppress progress output

    Returns:
        Rollback result log
    """
    rollback_log = {
        "executed_at": datetime.now().isoformat(),
        "dry_run": dry_run,
        "original_apply": log.get("executed_at", "unknown"),
        "operations": [],
        "stats": {
            "success": 0,
            "failed": 0,
            "skipped": 0,
        },
    }

    # Only rollback successful moves
    successful_ops = [
        op for op in log.get("operations", [])
        if op.get("status") == "success"
    ]

    if not quiet:
        print(f"Found {len(successful_ops)} operations to rollback", file=sys.stderr)

    # Reverse order to undo in reverse
    for op in reversed(successful_ops):
        source = Path(op["target"])  # Current location (was target)
        target = Path(op["source"])  # Original location (was source)

        result = {
            "source": str(source),
            "target": str(target),
            "status": "pending",
        }

        # Check if current file exists
        if not source.exists():
            result["status"] = "skipped"
            result["reason"] = "file not found at target location"
            rollback_log["operations"].append(result)
            rollback_log["stats"]["skipped"] += 1
            if not quiet:
                print(f"[SKIP] {source.name}: not found", file=sys.stderr)
            continue

        # Check if original location is occupied
        if target.exists():
            result["status"] = "skipped"
            result["reason"] = "original location occupied"
            rollback_log["operations"].append(result)
            rollback_log["stats"]["skipped"] += 1
            if not quiet:
                print(f"[SKIP] {source.name}: original location occupied", file=sys.stderr)
            continue

        try:
            if dry_run:
                result["status"] = "dry_run"
                if not quiet:
                    print(f"[DRY RUN] {source} -> {target}", file=sys.stderr)
            else:
                # Ensure parent directory exists
                target.parent.mkdir(parents=True, exist_ok=True)

                # Move back
                shutil.move(str(source), str(target))
                result["status"] = "success"

                if not quiet:
                    print(f"[RESTORED] {source.name} -> {target.parent.name}/", file=sys.stderr)

            rollback_log["stats"]["success"] += 1

        except Exception as e:
            result["status"] = "failed"
            result["error"] = str(e)
            rollback_log["stats"]["failed"] += 1
            if not quiet:
                print(f"[FAIL] {source.name}: {e}", file=sys.stderr)

        rollback_log["operations"].append(result)

    return rollback_log


def cleanup_empty_dirs(base_dir: Path, quiet: bool = False) -> int:
    """Remove empty category directories after rollback."""
    removed = 0
    for category_dir in base_dir.iterdir():
        if category_dir.is_dir() and not any(category_dir.iterdir()):
            try:
                category_dir.rmdir()
                removed += 1
                if not quiet:
                    print(f"[CLEANUP] Removed empty directory: {category_dir.name}", file=sys.stderr)
            except OSError:
                pass
    return removed


def main():
    parser = argparse.ArgumentParser(description="Rollback move operations from apply log.")
    parser.add_argument(
        "-i", "--input",
        type=Path,
        required=True,
        help="Input apply log JSON file"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output rollback log JSON file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate rollback without actually moving files"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove empty category directories after rollback"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output"
    )

    args = parser.parse_args()

    try:
        if not args.input.exists():
            raise FileNotFoundError(f"Log file not found: {args.input}")

        log = json.loads(args.input.read_text())

        if log.get("dry_run"):
            print("Warning: This log is from a dry run, nothing to rollback", file=sys.stderr)
            return 0

        if not args.quiet:
            mode = "[DRY RUN] " if args.dry_run else ""
            print(f"{mode}Rolling back operations...", file=sys.stderr)

        rollback_log = rollback_operations(log, dry_run=args.dry_run, quiet=args.quiet)

        if args.cleanup and not args.dry_run:
            target_base = Path(log.get("plan_source", ""))
            # Try to find target base from operations
            if rollback_log["operations"]:
                first_op = rollback_log["operations"][0]
                if "source" in first_op:
                    target_base = Path(first_op["source"]).parent.parent
                    cleanup_empty_dirs(target_base, quiet=args.quiet)

        if not args.quiet:
            print(f"\nResults: {rollback_log['stats']['success']} restored, "
                  f"{rollback_log['stats']['failed']} failed, "
                  f"{rollback_log['stats']['skipped']} skipped", file=sys.stderr)

        json_output = json.dumps(rollback_log, indent=2, ensure_ascii=False)

        if args.output:
            args.output.write_text(json_output)
            if not args.quiet:
                print(f"Log saved to {args.output}", file=sys.stderr)
        else:
            print(json_output)

        return 0 if rollback_log["stats"]["failed"] == 0 else 1

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
