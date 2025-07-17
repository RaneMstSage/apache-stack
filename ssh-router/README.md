# SSH Router Container

Custom SSH routing container for apache-stack infrastructure.

## Purpose

Routes SSH connections by username to different backend services:
- `admin@server` → Windows host SSH (admin access)
- `git@server` → Git repositories (future - Phase 2)
- `svn@server` → SVN repositories (future - Phase 3)

## Current Implementation

**Phase 1**: Windows SSH routing only
- Routes admin user SSH connections to Windows host on configurable port
- Maintains existing SSH key authentication
- Dynamic username configuration (no hardcoded usernames)

## Architecture

```
Internet:2222 → SSH Router Container → Windows Host:2221
```

## Configuration

### Environment Variables

**Required:**
- `ADMIN_USERNAME`: Username for both SSH router access and Windows target (set in .env)

**Optional:**
- `WINDOWS_SSH_HOST`: Target Windows host (default: host.docker.internal)
- `WINDOWS_SSH_PORT`: Windows SSH port (default: 2221)

### SSH Key Setup

1. Create SSH keys directory: `~/docker-volumes/ssh-router/keys/`
2. Copy your SSH public key to: `~/docker-volumes/ssh-router/keys/{ADMIN_USERNAME}_authorized_keys`
3. Format: One key per line, standard SSH authorized_keys format

Example:
```bash
# If ADMIN_USERNAME=sage, create:
~/docker-volumes/ssh-router/keys/sage_authorized_keys

# Content:
ssh-ed25519 AAAAC3N... My SSH Key
```

## Prerequisites

2. **Environment variables set in .env**:
   ```bash
   ADMIN_USERNAME=your_username
   ```

## Testing

```bash
# Test connection (should route to Windows host)
ssh {ADMIN_USERNAME}@code.mstsage.com -p 2222
```

## Security Features

- No hardcoded usernames in source code
- Dynamic user creation from environment variables
- SSH key authentication only (no passwords)
- Isolated container environment

## Future Phases

- **Phase 2**: Add Git repository routing with LDAP authorization
- **Phase 3**: Add SVN repository routing  
- **Phase 4**: Redmine SSH key management integration

## Troubleshooting

### Connection refused
- Check if Windows SSH is running on port 2221
- Verify container is running: `docker ps | grep ssh-router`

### Permission denied
- Verify SSH public key is in correct authorized_keys file
- Check file permissions: `chmod 600 authorized_keys`
- Confirm SSH_USERNAME matches authorized_keys filename

### Container won't start
- Check environment variables are set
- Review container logs: `docker logs ssh-router`