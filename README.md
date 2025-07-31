# Apache Stack with Nginx Reverse Proxy

This repository builds a comprehensive web application stack with Apache HTTPD 2.4.63 from source, with Nginx serving as a reverse proxy. The stack provides a unified entry point for all services while maintaining direct access capabilities for development and debugging.

## 🔧 Requirements
- Docker
- Docker Compose v2+
- Domain name(s) for SSL certificates (optional for development)
- Git LFS client (`git lfs version`)

## ✨ Features
- ✅ Nginx reverse proxy providing a unified entry point
- ✅ Automatic SSL certificate management with Let's Encrypt
- ✅ HTTP/2 support for improved performance
- ✅ LDAP centralized authentication with group-based access control
- ✅ SSH routing with dynamic database authentication
- ✅ Git repositories with full LFS support (SSH only)
- ✅ SVN repositories with collection-based organization
- ✅ Redmine integration with SSH key management
- ✅ Multi-instance Apache for load balancing
- ✅ Enhanced security with proper headers and timeouts

## 🏗️ Architecture Overview

```
   External Clients
         │
         ├─────────── Port 2222 ──→ [SSH Router]
         │                               │
         ▼                               ├→ Admin → Windows Host
      [Nginx]   ← Let's Encrypt         ├→ Git → Repositories (with LFS)
         │                               └→ SVN → Collections
         ├─────────┬──────────┬──────────┐
         │         │          │          │
         ▼         ▼          ▼          ▼
   [Apache 1-3]  [Redmine]   [LDAP]   [LFS Server]
      │ │
      │ └────────────────┐
      │                  │
      ▼                  ▼
 [PHP-FPM]       [Git/SVN/Python/Lua]
```

## 📋 Current Status

### ✅ Completed Features
- Full SSH routing with database authentication
- Git repositories with LFS support (SSH only, no HTTPS)
- SVN repositories with collection-based access
- LDAP group authorization
- Nginx reverse proxy with SSL
- Redmine integration for project management
- Dynamic SSH key management (no container restarts needed)
- MySQL database for Redmine and authentication
- Searxng private search engine integration

### 🚧 Known Limitations
- VS Code Remote SSH not yet configured for Git operations
- Workaround: Use terminal for Git operations or configure VS Code to use external terminal

### 📝 Important: Git Access Protocol
**All Git operations now use SSH protocol on port 2222. HTTPS access has been deprecated for security and to ensure proper LFS functionality.**

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/apache-stack.git
cd apache-stack
```

### 2. Set Up Environment Variables

Create a `.env` file with the following:

```bash
# Base directory for Docker volumes
DOCKER_VOLUMES_BASE=/home/yourusername/docker-volumes/apache-stack

# WSL paths for repositories (adjust for your system)
WSL_GIT_REPOS_PATH=/home/yourusername/repositories/git
WSL_SVN_REPOS_PATH=/home/yourusername/repositories/svn
WSL_GIT_LFS_PATH=/home/yourusername/repositories/git-lfs-storage

# Nginx ports
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443

# SSH Router
ADMIN_USERNAME=yourusername
WINDOWS_SSH_HOST=host.docker.internal
WINDOWS_SSH_PORT=2221
GIT_USERNAME=git
SVN_USERNAME=svn

# Apache ports (for direct access)
APACHE_HTTP_PORT=8080
APACHE_HTTPS_PORT=8443

# MySQL settings
MYSQL_ROOT_PASSWORD=your_secure_password
MYSQL_PORT=3306

# Redmine settings
REDMINE_PORT=3000
REDMINE_DB_DATABASE=redmine
REDMINE_DB_USERNAME=redmine
REDMINE_DB_PASSWORD=redmine_password
REDMINE_SECRET_KEY_BASE=generate_a_64_char_secret_key_here

# LDAP settings
LDAP_ORGANISATION=Your Organization
LDAP_DOMAIN=yourdomain.com
LDAP_ADMIN_PASSWORD=ldap_admin_password
LDAP_HOST=openldap
LDAP_PORT=389
LDAP_BASE_DN=dc=yourdomain,dc=com
LDAP_BIND_DN=cn=admin,dc=yourdomain,dc=com

# Searxng settings
SEARXNG_HTTP_PORT=8888
SEARXNG_BASE_URL=https://search.yourdomain.com/
SEARXNG_SECRET=generate_a_secret_key_here

# LFS Server
LFS_ADMINUSER=lfsadmin
LFS_ADMINPASS=lfs_admin_password
```

### 3. Create Directory Structure

```bash
# Set your volumes base directory
export DOCKER_VOLUMES_BASE="/home/yourusername/docker-volumes/apache-stack"

# Create all necessary directories
mkdir -p ${DOCKER_VOLUMES_BASE}/{nginx/{conf.d,ssl,logs,cache},certbot/{conf,www,logs}}
mkdir -p ${DOCKER_VOLUMES_BASE}/{conf,htdocs,var,uploads,php,python-apps}
mkdir -p ${DOCKER_VOLUMES_BASE}/redmine/{files,plugins,config,themes}
mkdir -p ${DOCKER_VOLUMES_BASE}/ssh-router/keys
mkdir -p ${DOCKER_VOLUMES_BASE}/searxng/{settings,data}

# Create repository directories
mkdir -p ~/repositories/{git,svn,git-lfs-storage}

# Set permissions
chmod -R 755 ${DOCKER_VOLUMES_BASE}
```

### 4. Configure Services

```bash
# Copy configuration templates
cp -r config-templates/* ${DOCKER_VOLUMES_BASE}/

# Create admin SSH key file
touch ${DOCKER_VOLUMES_BASE}/ssh-router/keys/${ADMIN_USERNAME}_authorized_keys
chmod 600 ${DOCKER_VOLUMES_BASE}/ssh-router/keys/${ADMIN_USERNAME}_authorized_keys
# Add your SSH public key to this file

# Create repository access configuration
cat > ${DOCKER_VOLUMES_BASE}/ssh-router/repo-access.conf << 'EOF'
[defaults.git]
read_groups = git-users,admins
write_groups = git-users,admins

[defaults.svn]
read_groups = svn-users,admins
write_groups = svn-users,admins
EOF
```

### 5. Start the Stack

```bash
# Build custom images
docker-compose build

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🔐 SSH Access Configuration

### For Users

1. **Add SSH Key in Redmine**:
    - Log into Redmine
    - Go to "My account" → "SSH Keys"
    - Add your SSH public key
    - Key is immediately available (no restart needed)

2. **Clone Repositories**:
   ```bash
   # Clone via SSH (port 2222)
   git clone ssh://git@yourdomain.com:2222/project/repo.git
   ```

3. **Convert Existing Repos to SSH**:
   ```bash
   # Change remote URL from HTTPS to SSH
   git remote set-url origin ssh://git@yourdomain.com:2222/project/repo.git
   ```

### For Administrators

1. **Admin SSH Access** (to Windows host):
   ```bash
   ssh yourusername@yourdomain.com -p 2222
   ```

2. **Manage Repository Access**:
    - Edit `${DOCKER_VOLUMES_BASE}/ssh-router/repo-access.conf`
    - Changes apply immediately (no restart needed)

## 📦 Git LFS Setup

### For New Repositories

```bash
cd your-repo
git lfs install

# Track large files
git lfs track "*.psd"
git lfs track "*.zip"
git lfs track "*.blend"

# Commit LFS config
git add .gitattributes
git commit -m "Configure Git LFS"
git push
```

### For Existing Repositories

```bash
# Install LFS and migrate existing large files
git lfs install
git lfs track "*.psd"
git lfs migrate import --include="*.psd" --everything
git push --force-with-lease
```

## 🛠️ Common Operations

### Service Management

```bash
# Restart a specific service
docker-compose restart nginx

# View service logs
docker-compose logs -f ssh-router

# Update images
docker-compose pull
docker-compose up -d
```

### SSL Certificate Management

```bash
# Obtain certificates (production)
docker-compose run --rm certbot certonly --webroot \
  -w /var/www/certbot -d yourdomain.com -d www.yourdomain.com \
  --email admin@yourdomain.com --agree-tos --no-eff-email

# Test renewal
docker-compose run --rm certbot renew --dry-run
```

### Database Backup

```bash
# Backup MySQL databases
docker-compose exec mysql sh -c \
  'mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" --all-databases' \
  > backups/mysql_$(date +%Y%m%d).sql

# Backup repositories
tar -czf backups/git_repos_$(date +%Y%m%d).tar.gz ~/repositories/git
tar -czf backups/svn_repos_$(date +%Y%m%d).tar.gz ~/repositories/svn
```

## 🐛 Troubleshooting

### SSH Connection Issues

```bash
# Test SSH authentication
ssh git@yourdomain.com -p 2222

# Check SSH router logs
docker-compose logs -f ssh-router

# Verify database key lookup
docker exec -it ssh-router /opt/scripts/get_ssh_keys.py git
```

### Git LFS Issues

```bash
# Check LFS status
git lfs status
git lfs ls-files

# Enable trace for debugging
GIT_TRACE=1 git lfs fetch
```

### Permission Issues

```bash
# Fix Apache content permissions
sudo chown -R daemon:daemon ${DOCKER_VOLUMES_BASE}/htdocs

# Fix repository permissions
sudo chown -R 1000:1002 ~/repositories/git
sudo chmod -R 775 ~/repositories/git
```

## 📚 Additional Documentation

- [SSH Router Details](./ssh-router/README.md)
- [Git LFS Setup Guide](./docs/GIT_LFS_SETUP.md)
- [LDAP Configuration](./docs/LDAP_CONFIG.md)
- [Nginx Configuration](./docs/NGINX_CONFIG.md)

## 🔒 Security Considerations

- All Git access via SSH (no HTTPS) for enhanced security
- SSH keys managed through Redmine database
- LDAP group-based authorization
- Admin SSH access uses static key file
- SSL certificates via Let's Encrypt
- Fail2ban integration recommended for production

## 📈 Performance Optimization

- Multi-instance Apache for load balancing
- Nginx caching for static assets
- PHP-FPM for better PHP performance
- Redis caching for Searxng
- Shared Git LFS storage

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Maintained by **@ranemstsage**