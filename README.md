# Downloads Detox

Automatically organize your Downloads folder by categorizing files into subdirectories based on file type.

## Features

- **Smart categorization**: Automatically sorts files into Documents, Images, Videos, Audio, Archives, Code, Apps, and Other
- **Dry-run mode**: Preview changes before executing
- **Rollback support**: Undo the last organization with a single command
- **SHA256 integrity**: Optional hash verification for moved files
- **Detailed logging**: JSON logs for scan results, move plans, and execution history

## Quick Start

```bash
# Preview what will happen (recommended first run)
./run.sh --dry-run

# Execute the organization
./run.sh

# Undo if needed
./run.sh --rollback
```

## Usage

```bash
./run.sh [options]

Options:
  --dry-run       Simulate without moving files
  --scan-only     Only scan, don't plan or apply
  --rollback      Undo the last apply operation
  --verify-hash   Verify file integrity after move
  --quiet, -q     Suppress progress output
  --help, -h      Show help
```

## File Categories

| Category   | Extensions                                           |
|------------|------------------------------------------------------|
| Documents  | .pdf, .doc, .docx, .txt, .rtf, .odt, .xls, .xlsx, .ppt, .pptx |
| Images     | .jpg, .jpeg, .png, .gif, .bmp, .svg, .webp, .ico, .tiff, .heic |
| Videos     | .mp4, .mov, .avi, .mkv, .wmv, .flv, .webm, .m4v     |
| Audio      | .mp3, .wav, .flac, .aac, .ogg, .m4a                 |
| Archives   | .zip, .tar, .gz, .rar, .7z, .bz2, .xz, .dmg        |
| Code       | .py, .js, .ts, .jsx, .tsx, .java, .cpp, .c, .h, .go, .rs, .rb, .php, .swift |
| Apps       | .app, .pkg, .dmg, .exe, .msi                        |
| Other      | Everything else                                      |

## Directory Structure

After running, your Downloads folder will look like:

```
~/Downloads/
├── Organized/
│   ├── Documents/
│   ├── Images/
│   ├── Videos/
│   ├── Audio/
│   ├── Archives/
│   ├── Code/
│   ├── Apps/
│   └── Other/
└── ... (remaining unorganized files)
```

## Configuration

Environment variables:

| Variable       | Default                      | Description                    |
|----------------|------------------------------|--------------------------------|
| `DOWNLOADS_DIR`| `~/Downloads`                | Directory to scan              |
| `TARGET_DIR`   | `~/Downloads/Organized`      | Where to move organized files  |
| `OUTPUT_DIR`   | `./output`                   | Where to save logs             |

Example:
```bash
DOWNLOADS_DIR=~/Desktop TARGET_DIR=~/Desktop/Sorted ./run.sh
```

## Individual Scripts

Each script can be run standalone:

```bash
# Scan and output JSON report
python3 scan.py -d ~/Downloads -o scan.json --hash

# Generate move plan from scan
python3 plan.py -i scan.json -o plan.json -t ~/Downloads/Organized

# Execute plan (with dry-run option)
python3 apply.py -i plan.json -o apply.log --dry-run

# Rollback from log
python3 rollback.py -i apply.log --cleanup
```

## Output Files

All operations generate JSON logs in the `output/` directory:

- `scan_YYYYMMDD_HHMMSS.json` - File inventory with metadata
- `plan_YYYYMMDD_HHMMSS.json` - Move operations to execute
- `apply_YYYYMMDD_HHMMSS.json` - Execution log (needed for rollback)
- `rollback_YYYYMMDD_HHMMSS.json` - Rollback operation log

## Requirements

- Python 3.7+
- macOS / Linux
- `jq` (optional, for summary display)

## License

MIT
