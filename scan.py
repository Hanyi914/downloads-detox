#!/usr/bin/env python3
"""
scan.py - Scan Downloads directory and categorize files by extension.
"""

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# File categories by extension
CATEGORIES = {
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico", ".tiff", ".heic"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".m4v"],
    "Archives": [".zip", ".tar", ".gz", ".rar", ".7z", ".bz2", ".xz", ".dmg"],
    "Code": [".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cpp", ".c", ".h", ".go", ".rs", ".rb", ".php", ".swift"],
    "Apps": [".app", ".pkg", ".dmg", ".exe", ".msi"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
}


def get_category(ext: str) -> str:
    """Get category for a file extension."""
    ext_lower = ext.lower()
    for category, extensions in CATEGORIES.items():
        if ext_lower in extensions:
            return category
    return "Other"


def compute_file_hash(filepath: Path, algorithm: str = "sha256") -> str:
    """Compute hash of a file for integrity checking."""
    hash_obj = hashlib.new(algorithm)
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except (IOError, PermissionError) as e:
        return f"ERROR:{e}"


def scan_directory(directory: Path, include_hash: bool = False) -> Dict[str, Any]:
    """
    Scan a directory and categorize all files.

    Args:
        directory: Path to scan
        include_hash: Whether to compute file hashes

    Returns:
        Dictionary with scan results
    """
    results: Dict[str, List[Dict[str, Any]]] = {cat: [] for cat in list(CATEGORIES.keys()) + ["Other"]}

    stats = {
        "total_files": 0,
        "total_size": 0,
        "by_category": {},
    }

    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    for item in directory.iterdir():
        if item.is_file():
            ext = item.suffix
            category = get_category(ext)

            file_info = {
                "name": item.name,
                "path": str(item.absolute()),
                "extension": ext,
                "size": item.stat().st_size,
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat(),
                "category": category,
            }

            if include_hash:
                file_info["sha256"] = compute_file_hash(item)

            results[category].append(file_info)
            stats["total_files"] += 1
            stats["total_size"] += file_info["size"]

    # Compute category stats
    for category, files in results.items():
        if files:
            stats["by_category"][category] = {
                "count": len(files),
                "size": sum(f["size"] for f in files),
            }

    return {
        "scan_time": datetime.now().isoformat(),
        "directory": str(directory.absolute()),
        "stats": stats,
        "files": results,
    }


def main():
    parser = argparse.ArgumentParser(description="Scan Downloads directory and categorize files.")
    parser.add_argument(
        "-d", "--directory",
        type=Path,
        default=Path.home() / "Downloads",
        help="Directory to scan (default: ~/Downloads)"
    )
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Output file for JSON report (default: stdout)"
    )
    parser.add_argument(
        "--hash",
        action="store_true",
        help="Include SHA256 hash for each file"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress progress output"
    )

    args = parser.parse_args()

    try:
        if not args.quiet:
            print(f"Scanning {args.directory}...", file=sys.stderr)

        results = scan_directory(args.directory, include_hash=args.hash)

        if not args.quiet:
            print(f"Found {results['stats']['total_files']} files", file=sys.stderr)

        json_output = json.dumps(results, indent=2, ensure_ascii=False)

        if args.output:
            args.output.write_text(json_output)
            if not args.quiet:
                print(f"Report saved to {args.output}", file=sys.stderr)
        else:
            print(json_output)

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
