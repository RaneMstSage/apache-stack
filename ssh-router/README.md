# SSH Router Container

Custom SSH routing container for apache-stack infrastructure with dynamic database authentication.

## Purpose

Routes SSH connections by username to different backend services:
- `admin@server` → Windows host SSH (admin access) ✅ **Active**
- `git@server` → Git repositories with LDAP authorization ✅ **Active**
- `svn@server` → SVN repositories with LDAP authorization ✅ **Active**

## Current Implementation (Phase 1 Complete)

### ✅ Dynamic SSH Key Authentication
- **Git/SVN users**: SSH keys fetched dynamically from Redmine's `sage_ssh_keys` table
- **Admin user**: Static key file for enhanced security
- **No container restart needed** when users add/remove SSH keys in Redmine

### ✅ Multi-service SSH Routing
- Routes admin SSH connections to Windows host for system administration
- Routes Git SSH connections with full Git LFS support over SSH
- Routes SVN SSH connections to Subversion repositories
- All routing based on username (sage@, git@, svn@)

### ✅ Integrated Authentication Flow
1. SSH connection received on port 2222
2. For git/svn users: `get_ssh_keys.py` queries Redmine database for authorized keys
3. SSH authenticates using database keys
4. Proxy scripts identify user via SSH key fingerprint
5. LDAP groups determine repository access permissions

### ✅ Git LFS Support
- Full Git LFS support over SSH protocol
- Shared LFS storage at `/usr/local/git-lfs-storage`
- Automatic LFS detection and routing
- Works seamlessly with `git clone`, `git pull`, `git push`

## Architecture

```
Internet:2222 → SSH Router Container
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
Windows Host    Git Repos      SVN Repos
(port 2221)    (with LFS)     (collections)
```

## Configuration

### Environment Variables

**Required:**
- `ADMIN_USERNAME`: Admin user for Windows access
- `MYSQL_HOST`, `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`: Redmine database
- `LDAP_HOST`, `LDAP_BASE_DN`, `LDAP_BIND_DN`, `LDAP_BIND_PASSWORD`: LDAP config

**Optional:**
- `WINDOWS_SSH_HOST`: Target Windows host (default: host.docker.internal)
- `WINDOWS_SSH_PORT`: Windows SSH port (default: 2221)
- `GIT_USERNAME`: Git service user (default: git)
- `SVN_USERNAME`: SVN service user (default: svn)

### Admin SSH Key Setup

Admin keys are still file-based for security:

```bash
# Create admin key file
~/docker-volumes/ssh-router/keys/sage_authorized_keys

# Add your SSH public key (one per line)
ssh-ed25519 AAAAC3N... admin@example.com
```

### Git/SVN User Setup

Users manage their SSH keys through Redmine:
1. Log into Redmine
2. Go to "My account" → "SSH Keys"
3. Add SSH public key
4. Key is immediately available (no restart needed)

## Repository Access Control

### Current Implementation
Repository access is controlled via configuration file:
`~/docker-volumes/ssh-router/repo-access.conf`

```ini
[defaults.git]
read_groups = git-users,admins
write_groups = git-users,admins

[git.apache-stack]
groups = proj-infrastructure,admins

[git.UnityRPG_Heroes]
owner = rane_mstsage
admin_groups = proj-gamedev,admins
```

### Access Rules
- **Personal repositories**: Owner has full access
- **Project repositories**: LDAP group membership required
- **Admins**: Access to all repositories

## Git Repository Setup

### Converting Existing Repository to SSH

```bash
# Change remote URL from HTTPS to SSH
git remote set-url origin ssh://git@code.mstsage.com:2222/project/repo.git

# For upstream remotes
git remote set-url upstream ssh://git@code.mstsage.com:2222/organization/repo.git

# Verify changes
git remote -v
```

### Cloning New Repository

```bash
# Clone via SSH (no more HTTPS!)
git clone ssh://git@code.mstsage.com:2222/project/repo.git
```

### Setting Up Git LFS

For new repositories:
```bash
# Initialize LFS in your repository
git lfs install

# Track file types
git lfs track "*.psd"
git lfs track "*.blend"
git lfs track "*.fbx"

# Commit .gitattributes
git add .gitattributes
git commit -m "Add LFS tracking"
```

For existing repositories with large files:
```bash
# Install LFS
git lfs install

# Track and migrate existing files
git lfs track "*.psd"
git lfs migrate import --include="*.psd" --everything

# Push with LFS
git push --force-with-lease
```

## Testing SSH Access

```bash
# Test Git access (should show "No Git command provided")
ssh git@code.mstsage.com -p 2222

# Test admin access (routes to Windows)
ssh sage@code.mstsage.com -p 2222

# Test Git operations
git clone ssh://git@code.mstsage.com:2222/test-repo.git
cd test-repo
echo "test" > test.txt
git add test.txt
git commit -m "Test commit"
git push
```

## Troubleshooting

### SSH Key Not Recognized
1. Check key is active in Redmine: "My account" → "SSH Keys"
2. Verify key format (must be single line)
3. Check container logs: `docker-compose logs -f ssh-router`
4. Test database query: `docker exec -it ssh-router /opt/scripts/get_ssh_keys.py git`

### Permission Denied on Repository
1. Verify LDAP group membership
2. Check repository configuration in `repo-access.conf`
3. Ensure repository exists and has correct permissions
4. Review logs for LDAP authentication issues

### Connection Reset Errors
- Check container health: `docker-compose ps ssh-router`
- Review memory usage: `docker stats ssh-router`
- Check for rate limiting or firewall rules
- Verify network connectivity

### Git LFS Issues
1. Ensure LFS is installed: `git lfs version`
2. Check LFS tracking: `git lfs ls-files`
3. Verify LFS storage is accessible
4. Test with: `GIT_TRACE=1 git lfs fetch --all`

## Security Features

- **Database-driven authentication** for Git/SVN (dynamic, manageable)
- **Static file authentication** for admin access (secure, controlled)
- **SSH key fingerprint matching** to identify users
- **LDAP group authorization** for repository access
- **No password authentication** (key-only)
- **Isolated container environment**
- **Audit logging** of all access attempts

## Implementation Details

### Key Components
1. **`get_ssh_keys.py`**: Fetches authorized keys from Redmine database
2. **`git_proxy.py`**: Routes Git commands, handles LFS, checks LDAP groups
3. **`svn_proxy.py`**: Routes SVN commands, checks LDAP authorization
4. **`windows_proxy.py`**: Proxies admin connections to Windows host
5. **`repo_config.py`**: Loads repository access configuration

### Database Schema
SSH keys stored in Redmine's `sage_ssh_keys` table:
- `user_id`: Links to Redmine user
- `key`: SSH public key
- `fingerprint`: SHA256 fingerprint for lookup
- `active`: Boolean flag
- `title`: Key description

## Future Improvements (Phase 2)

- [ ] Web-based repository access management UI
- [ ] Dynamic configuration reload without restart
- [ ] Repository creation API with automatic access setup
- [ ] Integration with Redmine project permissions
- [ ] Audit log visualization
- [ ] Multi-factor authentication support
- [ ] SSH certificate authority implementation

## Maintenance

### Viewing Active Keys
```bash
# See all active SSH keys in the system
docker exec -it ssh-router /opt/scripts/get_ssh_keys.py git | wc -l
```

### Updating Repository Access
1. Edit `~/docker-volumes/ssh-router/repo-access.conf`
2. No restart needed - changes apply immediately

### Container Logs
```bash
# View real-time logs
docker-compose logs -f ssh-router

# Check authentication attempts
docker-compose logs ssh-router | grep "Access granted"
```

---

This SSH router provides a secure, maintainable solution for repository access with seamless Git LFS support and dynamic key management through Redmine.