#!/bin/bash
cd "$(dirname "$0")"
clear
echo "DRAG WEAR IRON v0.16 — WEAR IT ALL"
echo "Mac launcher"
echo ""
chmod +x run.sh INSTALL.command
./run.sh
status=$?
echo ""
if [ $status -ne 0 ]; then echo "DRAG WEAR IRON stopped with an error."; fi
echo ""
read -n 1 -s -r -p "Press any key to close this window..."
