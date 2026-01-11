#!/bin/bash
cd "$(dirname "$0")"
/usr/bin/python3 scan.py -d "$HOME/Downloads" -o output/scheduled_scan.json -q
/usr/bin/python3 plan.py -i output/scheduled_scan.json -o output/scheduled_plan.json -t "$HOME/Downloads/Organized" -q
/usr/bin/python3 apply.py -i output/scheduled_plan.json -o output/scheduled_apply.json -q
echo "$(date): Detox completed" >> /tmp/downloads-detox.log
