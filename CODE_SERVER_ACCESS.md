# Code-Server Access Configuration

## Overview

Code-Server (Web IDE) is accessible in two ways:

1. **Via Nginx** (recommended): `http://<host-ip>` (port 80)
2. **Direct access**: `http://<host-ip>:${CODE_SERVER_PORT:-8080}` (default port 8080)

## Configuration

### Port Configuration

The direct access port is configurable via `.env` file:

```bash
# In .env file
CODE_SERVER_PORT=8080  # Default port, change if needed
```

### Network Binding

Code-Server is bound to `0.0.0.0`, making it accessible on:
- ✅ All host network interfaces
- ✅ All host IP addresses
- ✅ Localhost (127.0.0.1)
- ✅ LAN IP addresses (e.g., 192.168.1.100)
- ✅ Public IP addresses (if exposed)

## Access Methods

### Method 1: Via Nginx (Recommended)
```
http://localhost
http://<host-ip>
```
- Port: 80
- Benefits: Single entry point, SSL support (when configured)
- Use when: Accessing from browser, want unified access

### Method 2: Direct Access
```
http://localhost:8080
http://<host-ip>:8080
http://<any-host-ip>:8080
```
- Port: Configurable (default 8080)
- Benefits: Direct access, bypasses Nginx
- Use when: Need direct access, debugging, or custom port

## Examples

### Local Access
```bash
# Via Nginx
http://localhost

# Direct
http://localhost:8080
```

### LAN Access
```bash
# If host IP is 192.168.1.100

# Via Nginx
http://192.168.1.100

# Direct
http://192.168.1.100:8080
```

### Custom Port
```bash
# In .env file
CODE_SERVER_PORT=9000

# Access via
http://<host-ip>:9000
```

## Security Considerations

### Firewall
If accessing from remote networks, ensure firewall allows:
- Port 80 (Nginx)
- Port ${CODE_SERVER_PORT} (Code-Server direct)

### Authentication
Code-Server requires password authentication (configured in `.env`):
```bash
CODE_SERVER_PASSWORD=your_secure_password
```

### Network Isolation
- Code-Server listens on all interfaces (0.0.0.0)
- Consider firewall rules for production use
- Use VPN or SSH tunnel for remote access in sensitive environments

## Troubleshooting

### Port Already in Use
If port 8080 is already in use:
1. Change `CODE_SERVER_PORT` in `.env`
2. Restart services: `docker compose restart code-server`

### Cannot Access from Remote
1. Check firewall: `sudo ufw status`
2. Verify port binding: `sudo netstat -tlnp | grep 8080`
3. Check Docker port mapping: `docker ps | grep code-server`
4. Verify host IP: `ip addr show` or `hostname -I`

### Connection Refused
1. Verify Code-Server is running: `docker compose ps code-server`
2. Check logs: `docker compose logs code-server`
3. Verify port configuration in `.env`
4. Restart service: `docker compose restart code-server`

## Configuration Files

### docker-compose.yml
```yaml
ports:
  - "0.0.0.0:${CODE_SERVER_PORT:-8080}:8080"
```

### .env
```bash
CODE_SERVER_PORT=8080
CODE_SERVER_PASSWORD=your_password
```

## Summary

✅ **Accessible on all host IP addresses**  
✅ **Port configurable via .env** (default: 8080)  
✅ **Two access methods**: Via Nginx (port 80) or direct (port ${CODE_SERVER_PORT})  
✅ **Secure**: Password authentication required  

