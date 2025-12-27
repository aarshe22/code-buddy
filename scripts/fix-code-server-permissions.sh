#!/bin/bash

# Fix Code-Server Volume Permissions
# This script fixes permissions on code-server volumes

echo "=========================================="
echo "Fixing Code-Server Volume Permissions"
echo "=========================================="
echo ""

# Stop code-server container
echo "Stopping code-server container..."
docker compose stop code-server 2>/dev/null || true

# Fix permissions on config volume
echo "Fixing permissions on code-server-config volume..."
docker run --rm \
  -v code-buddy-code-server-config:/data \
  alpine sh -c "chown -R 1000:1000 /data && chmod -R 755 /data" 2>/dev/null || {
    echo "Warning: Could not fix config volume permissions"
    echo "You may need to remove and recreate the volume:"
    echo "  docker volume rm code-buddy-code-server-config"
}

# Fix permissions on data volume
echo "Fixing permissions on code-server-data volume..."
docker run --rm \
  -v code-buddy-code-server-data:/data \
  alpine sh -c "chown -R 1000:1000 /data && chmod -R 755 /data" 2>/dev/null || {
    echo "Warning: Could not fix data volume permissions"
}

# Fix permissions on extensions volume
echo "Fixing permissions on code-server-extensions volume..."
docker run --rm \
  -v code-buddy-code-server-extensions:/data \
  alpine sh -c "chown -R 1000:1000 /data && chmod -R 755 /data" 2>/dev/null || {
    echo "Warning: Could not fix extensions volume permissions"
}

# Fix permissions on logs volume
echo "Fixing permissions on code-server-logs volume..."
docker run --rm \
  -v code-buddy-code-server-logs:/data \
  alpine sh -c "chown -R 1000:1000 /data && chmod -R 755 /data" 2>/dev/null || {
    echo "Warning: Could not fix logs volume permissions"
}

echo ""
echo "=========================================="
echo "Permissions Fixed!"
echo "=========================================="
echo ""
echo "You can now restart code-server:"
echo "  docker compose up -d code-server"
echo ""

