#!/bin/bash

# Backup Script for Dev Stack Volumes
# Backs up all Docker volumes to ensure data persistence

set -e

BACKUP_DIR="${BACKUP_DIR:-backups/$(date +%Y%m%d_%H%M%S)}"
BACKUP_NAME="dev-stack-backup-$(date +%Y%m%d_%H%M%S).tar.gz"

echo "=========================================="
echo "Dev Stack Volume Backup"
echo "=========================================="
echo ""

# Create backup directory
mkdir -p "$BACKUP_DIR"
echo "Backup directory: $BACKUP_DIR"
echo ""

# Get all dev-stack volumes
VOLUMES=$(docker volume ls -q | grep -E "^dev-stack_|^devstack_" || docker volume ls -q | grep -E ".*ollama-data|.*code-server|.*agent|.*mcp|.*qdrant|.*indexer|.*rag|.*rules|.*api-gateway|.*nginx" || true)

if [ -z "$VOLUMES" ]; then
    echo "No dev-stack volumes found. Listing all volumes:"
    docker volume ls
    echo ""
    read -p "Enter volume names to backup (space-separated, or press Enter to exit): " VOLUMES
    if [ -z "$VOLUMES" ]; then
        echo "No volumes specified. Exiting."
        exit 0
    fi
fi

echo "Found volumes to backup:"
echo "$VOLUMES" | tr ' ' '\n' | while read vol; do
    if [ ! -z "$vol" ]; then
        echo "  - $vol"
    fi
done
echo ""

# Confirm
read -p "Proceed with backup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Backup cancelled."
    exit 0
fi

echo ""
echo "Starting backup..."
echo ""

# Backup each volume
BACKED_UP=0
FAILED=0

for volume in $VOLUMES; do
    if [ -z "$volume" ]; then
        continue
    fi
    
    echo -n "Backing up $volume... "
    
    # Check if volume exists
    if ! docker volume inspect "$volume" &>/dev/null; then
        echo "SKIPPED (volume does not exist)"
        continue
    fi
    
    # Create backup
    if docker run --rm \
        -v "$volume":/data:ro \
        -v "$(pwd)/$BACKUP_DIR":/backup \
        alpine tar czf "/backup/${volume}.tar.gz" -C /data . 2>/dev/null; then
        echo "✓ DONE"
        ((BACKED_UP++))
    else
        echo "✗ FAILED"
        ((FAILED++))
    fi
done

echo ""
echo "=========================================="
echo "Backup Summary"
echo "=========================================="
echo "Backed up: $BACKED_UP volumes"
echo "Failed: $FAILED volumes"
echo "Backup location: $BACKUP_DIR"
echo ""

# Create manifest
cat > "$BACKUP_DIR/MANIFEST.txt" <<EOF
Dev Stack Backup Manifest
========================
Date: $(date)
Backup Directory: $BACKUP_DIR

Volumes Backed Up:
$(echo "$VOLUMES" | tr ' ' '\n' | grep -v '^$' | nl)

Total: $BACKED_UP volumes
Failed: $FAILED volumes

To restore:
1. Stop services: docker compose down
2. Restore volumes using restore-volumes.sh
3. Start services: docker compose up -d
EOF

echo "Manifest created: $BACKUP_DIR/MANIFEST.txt"
echo ""
echo "Backup complete!"
echo ""
echo "To create a compressed archive:"
echo "  tar czf $BACKUP_NAME -C $(dirname "$BACKUP_DIR") $(basename "$BACKUP_DIR")"
echo ""

