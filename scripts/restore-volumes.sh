#!/bin/bash

# Restore Script for Dev Stack Volumes
# Restores Docker volumes from backup

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup-directory>"
    echo ""
    echo "Example:"
    echo "  $0 backups/20240101_120000"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Backup directory not found: $BACKUP_DIR"
    exit 1
fi

echo "=========================================="
echo "Dev Stack Volume Restore"
echo "=========================================="
echo ""
echo "Backup directory: $BACKUP_DIR"
echo ""

# Check for manifest
if [ -f "$BACKUP_DIR/MANIFEST.txt" ]; then
    echo "Found backup manifest:"
    cat "$BACKUP_DIR/MANIFEST.txt"
    echo ""
fi

# Find backup files
BACKUP_FILES=$(find "$BACKUP_DIR" -name "*.tar.gz" -type f)

if [ -z "$BACKUP_FILES" ]; then
    echo "Error: No backup files found in $BACKUP_DIR"
    exit 1
fi

echo "Found backup files:"
echo "$BACKUP_FILES" | while read file; do
    volume_name=$(basename "$file" .tar.gz)
    echo "  - $volume_name"
done
echo ""

# Confirm
echo "WARNING: This will overwrite existing volumes!"
read -p "Proceed with restore? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo "Stopping services..."
docker compose down 2>/dev/null || true

echo ""
echo "Starting restore..."
echo ""

RESTORED=0
FAILED=0

for backup_file in $BACKUP_FILES; do
    volume_name=$(basename "$backup_file" .tar.gz)
    
    echo -n "Restoring $volume_name... "
    
    # Create volume if it doesn't exist
    if ! docker volume inspect "$volume_name" &>/dev/null; then
        docker volume create "$volume_name" >/dev/null
    fi
    
    # Restore volume
    if docker run --rm \
        -v "$volume_name":/data \
        -v "$(pwd)/$BACKUP_DIR":/backup \
        alpine sh -c "cd /data && tar xzf /backup/$(basename "$backup_file")" 2>/dev/null; then
        echo "✓ DONE"
        ((RESTORED++))
    else
        echo "✗ FAILED"
        ((FAILED++))
    fi
done

echo ""
echo "=========================================="
echo "Restore Summary"
echo "=========================================="
echo "Restored: $RESTORED volumes"
echo "Failed: $FAILED volumes"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "Restore complete! You can now start services:"
    echo "  docker compose up -d"
else
    echo "Some volumes failed to restore. Please check the errors above."
fi
echo ""

