#!/bin/bash
#
# run.sh - Orchestrate Downloads Detox: scan → plan → apply
#
# Usage:
#   ./run.sh                    # Full run (scan, plan, apply)
#   ./run.sh --dry-run          # Simulate without moving files
#   ./run.sh --scan-only        # Only scan, don't plan or apply
#   ./run.sh --rollback         # Rollback last apply
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOWNLOADS_DIR="${DOWNLOADS_DIR:-$HOME/Downloads}"
OUTPUT_DIR="${OUTPUT_DIR:-$SCRIPT_DIR/output}"
TARGET_DIR="${TARGET_DIR:-$DOWNLOADS_DIR/Organized}"

# Parse arguments
DRY_RUN=""
SCAN_ONLY=""
ROLLBACK=""
QUIET=""
VERIFY_HASH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN="--dry-run"
            shift
            ;;
        --scan-only)
            SCAN_ONLY="true"
            shift
            ;;
        --rollback)
            ROLLBACK="true"
            shift
            ;;
        --quiet|-q)
            QUIET="--quiet"
            shift
            ;;
        --verify-hash)
            VERIFY_HASH="--verify-hash"
            shift
            ;;
        --help|-h)
            echo "Downloads Detox - Organize your Downloads folder"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --dry-run       Simulate without moving files"
            echo "  --scan-only     Only scan, don't plan or apply"
            echo "  --rollback      Rollback last apply"
            echo "  --quiet, -q     Suppress progress output"
            echo "  --verify-hash   Verify file integrity after move"
            echo "  --help, -h      Show this help"
            echo ""
            echo "Environment variables:"
            echo "  DOWNLOADS_DIR   Directory to scan (default: ~/Downloads)"
            echo "  OUTPUT_DIR      Output directory for logs (default: ./output)"
            echo "  TARGET_DIR      Target directory for organized files"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Timestamp for this run
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo "========================================"
echo "Downloads Detox - $(date)"
echo "========================================"
echo "Source: $DOWNLOADS_DIR"
echo "Target: $TARGET_DIR"
echo "Output: $OUTPUT_DIR"
echo ""

# Handle rollback
if [[ -n "$ROLLBACK" ]]; then
    LATEST_LOG=$(ls -t "$OUTPUT_DIR"/apply_*.json 2>/dev/null | head -1)
    if [[ -z "$LATEST_LOG" ]]; then
        echo "Error: No apply log found to rollback"
        exit 1
    fi
    echo "Rolling back from: $LATEST_LOG"
    python3 "$SCRIPT_DIR/rollback.py" \
        -i "$LATEST_LOG" \
        -o "$OUTPUT_DIR/rollback_${TIMESTAMP}.json" \
        $DRY_RUN $QUIET --cleanup
    echo ""
    echo "Rollback complete!"
    exit 0
fi

# Step 1: Scan
echo "[1/3] Scanning $DOWNLOADS_DIR..."
SCAN_FILE="$OUTPUT_DIR/scan_${TIMESTAMP}.json"
python3 "$SCRIPT_DIR/scan.py" \
    -d "$DOWNLOADS_DIR" \
    -o "$SCAN_FILE" \
    --hash \
    $QUIET

if [[ -n "$SCAN_ONLY" ]]; then
    echo ""
    echo "Scan complete! Results saved to: $SCAN_FILE"
    exit 0
fi

# Step 2: Plan
echo "[2/3] Generating move plan..."
PLAN_FILE="$OUTPUT_DIR/plan_${TIMESTAMP}.json"
python3 "$SCRIPT_DIR/plan.py" \
    -i "$SCAN_FILE" \
    -o "$PLAN_FILE" \
    -t "$TARGET_DIR" \
    $QUIET

# Step 3: Apply
echo "[3/3] Applying plan..."
APPLY_LOG="$OUTPUT_DIR/apply_${TIMESTAMP}.json"
python3 "$SCRIPT_DIR/apply.py" \
    -i "$PLAN_FILE" \
    -o "$APPLY_LOG" \
    $DRY_RUN $VERIFY_HASH $QUIET

echo ""
echo "========================================"
echo "Downloads Detox Complete!"
echo "========================================"
echo "Scan:  $SCAN_FILE"
echo "Plan:  $PLAN_FILE"
echo "Log:   $APPLY_LOG"
echo ""
echo "To rollback: $0 --rollback"

# Print summary from apply log
if command -v jq &> /dev/null; then
    echo ""
    echo "Summary:"
    jq -r '.stats | "  Success: \(.success)\n  Failed: \(.failed)\n  Skipped: \(.skipped)"' "$APPLY_LOG"
fi
