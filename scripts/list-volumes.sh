#!/bin/bash

# List all Code Buddy volumes with sizes

echo "=========================================="
echo "Code Buddy Volumes"
echo "=========================================="
echo ""

# Get all code-buddy volumes
VOLUMES=$(docker volume ls -q | grep -E "^code-buddy_" || docker volume ls -q)

if [ -z "$VOLUMES" ]; then
    echo "No volumes found."
    exit 0
fi

echo "Volume Name | Size | Mountpoint"
echo "-----------|------|------------"

for volume in $VOLUMES; do
    if [ -z "$volume" ]; then
        continue
    fi
    
    # Get volume info
    VOL_INFO=$(docker volume inspect "$volume" 2>/dev/null)
    if [ $? -eq 0 ]; then
        MOUNTPOINT=$(echo "$VOL_INFO" | grep -oP '(?<="Mountpoint": ")[^"]*')
        SIZE=$(du -sh "$MOUNTPOINT" 2>/dev/null | cut -f1 || echo "unknown")
        echo "$volume | $SIZE | $MOUNTPOINT"
    fi
done

echo ""
echo "Total volumes: $(echo "$VOLUMES" | wc -w)"
echo ""
echo "To see detailed information:"
echo "  docker volume inspect <volume-name>"
echo ""
echo "To see disk usage:"
echo "  docker system df -v"
echo ""

