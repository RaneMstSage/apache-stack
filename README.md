# Apache Stack with Nginx Reverse Proxy

This repository builds a comprehensive web application stack with Apache HTTPD 2.4.63 from source, with Nginx serving as a reverse proxy. The stack provides a unified entry point for all services while maintaining direct access capabilities for development and debugging.

## 🔧 Requirements
- Docker
- Docker Compose v2+
- Domain name(s) for SSL certificates (optional for development)

## ✨ New Features
- ✅ Nginx reverse proxy providing a unified entry point
- ✅ Automatic SSL certificate management with Let's Encrypt
- ✅ HTTP/2 support for improved performance
- ✅ LDAP proxying for centralized authentication
- ✅ Hostname-based routing to different services
- ✅ Optimized caching for static assets
- ✅ Enhanced security with proper headers and timeouts

## 🏗️ Architecture Overview

```
   External Clients
         │
         ▼
      [Nginx]   ← Let's Encrypt Certificates
         │
         ├─────────┬──────────┬──────────┐
         │         │          │          │
         ▼         ▼          ▼          ▼
   [Apache]    [Redmine]   [LDAP]    [Other Services]
      │ │
      │ └────────────────┐
      │                  │
      ▼                  ▼
 [PHP-FPM]       [Git/SVN/Python/Lua]
```

Nginx serves as the entrypoint, routing requests to the appropriate backend service based on hostname or URL path. Apache continues to host PHP applications, Git/SVN repositories, and more.

## 📋 Setup Guide

### 1. Directory Structure Setup

Create the necessary directory structure:

```bash
# Set your volumes base directory (update this to your preferred location)
export DOCKER_VOLUMES_BASE="/path/to/your/volumes/apache-stack"

# Create Nginx directories
mkdir -p ${DOCKER_VOLUMES_BASE}/nginx/{conf.d,ssl,logs,cache,error_pages}

# Create Certbot directories for Let's Encrypt
mkdir -p ${DOCKER_VOLUMES_BASE}/certbot/{conf,www,logs}

# Set proper permissions
chmod -R 755 ${DOCKER_VOLUMES_BASE}/nginx
chmod -R 755 ${DOCKER_VOLUMES_BASE}/certbot
```

### 2. Configuration Files

Copy the default Nginx configuration files from the `config-templates/nginx` directory:

```bash
# Copy all configuration files
cp config-templates/nginx/nginx.conf ${DOCKER_VOLUMES_BASE}/nginx/
cp config-templates/nginx/stream.conf ${DOCKER_VOLUMES_BASE}/nginx/
cp config-templates/nginx/conf.d/* ${DOCKER_VOLUMES_BASE}/nginx/conf.d/
cp config-templates/nginx/error_pages/* ${DOCKER_VOLUMES_BASE}/nginx/error_pages/

# Create 502.html error page (or copy it from the template directory)
cp config-templates/nginx/502.html ${DOCKER_VOLUMES_BASE}/nginx/
```

### 3. SSL Certificate Setup

For development environments, create a self-signed certificate:

```bash
# Generate a self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ${DOCKER_VOLUMES_BASE}/nginx/ssl/default.key \
  -out ${DOCKER_VOLUMES_BASE}/nginx/ssl/default.crt \
  -subj "/CN=localhost"

# Set proper permissions
chmod 600 ${DOCKER_VOLUMES_BASE}/nginx/ssl/default.key
chmod 644 ${DOCKER_VOLUMES_BASE}/nginx/ssl/default.crt
```

### 4. Setup Docker Environment

Create or modify your `.env` file to include the following variables:

```bash
# Nginx ports
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443

# LDAP ports (proxied through Nginx)
LDAP_PORT=389
LDAPS_PORT=636

# Apache ports (for direct access)
APACHE_HTTP_PORT=8080
APACHE_HTTPS_PORT=8443

# MySQL settings
MYSQL_ROOT_PASSWORD=your_secure_password
MYSQL_DATABASE=apache_stack
MYSQL_USER=apache_user
MYSQL_PASSWORD=apache_password

# Redmine database settings
REDMINE_DB_DATABASE=redmine
REDMINE_DB_USERNAME=redmine
REDMINE_DB_PASSWORD=redmine_password
REDMINE_SECRET_KEY_BASE=generate_a_secret_key_here

# LDAP settings
LDAP_ORGANISATION="Your Company"
LDAP_DOMAIN="example.org"
LDAP_ADMIN_PASSWORD=ldap_admin_password

# Base directory for volume mappings
DOCKER_VOLUMES_BASE=/path/to/your/volumes/apache-stack
```

### 5. Start the Stack

```bash
# Start the stack
docker-compose up -d

# Verify that all services are running
docker-compose ps
```

### 6. Obtain SSL Certificates (For Production)

For production environments with a real domain:

```bash
# Replace example.com with your actual domain name
docker-compose run --rm certbot certonly --webroot -w /var/www/certbot \
  -d example.com -d www.example.com \
  --email admin@example.com --agree-tos --no-eff-email

# Reload Nginx to apply the new certificates
docker-compose exec nginx nginx -s reload
```

After obtaining certificates, update your Nginx configuration to use them:

```bash
# Edit the SSL server blocks in your configuration to use the new certificates
# Example path: ${DOCKER_VOLUMES_BASE}/nginx/conf.d/apache-ssl.conf

# Reload Nginx after making changes
docker-compose exec nginx nginx -s reload
```

## 📝 Common Operations

### Testing Your Setup

Once the stack is running, you can access your services:

- Main Apache site: `http://localhost/`
- Direct Apache access: `http://localhost:8080/`
- Redmine: `http://redmine.localhost/`
- LDAP access: Configure your LDAP client to connect to `ldap://localhost:389`

### Managing Data Directories

The following directories contain persistent data:

- Apache content: `${DOCKER_VOLUMES_BASE}/htdocs/`
- Apache configuration: `${DOCKER_VOLUMES_BASE}/conf/`
- Redmine files: `${DOCKER_VOLUMES_BASE}/redmine/files/`
- Redmine configuration: `${DOCKER_VOLUMES_BASE}/redmine/config/`

Make sure these directories have appropriate permissions:

```bash
# For Apache-related directories
sudo chown -R daemon:daemon ${DOCKER_VOLUMES_BASE}/htdocs
sudo chown -R daemon:daemon ${DOCKER_VOLUMES_BASE}/uploads
sudo chown -R daemon:daemon ${DOCKER_VOLUMES_BASE}/var

# For Redmine directories
sudo chown -R 999:999 ${DOCKER_VOLUMES_BASE}/redmine
```

### Checking Logs

```bash
# Nginx logs
docker-compose exec nginx cat /var/log/nginx/error.log
docker-compose exec nginx cat /var/log/nginx/access.log

# Apache logs
docker-compose exec apache cat /usr/local/apache2/logs/error_log

# Certbot logs
docker-compose exec certbot cat /var/log/letsencrypt/letsencrypt.log
```

### Certificate Renewal Testing

To test certificate renewal (without actually renewing):

```bash
docker-compose run --rm certbot certonly --webroot -w /var/www/certbot \
  -d example.com --dry-run
```

## 🛡️ Security Considerations

- Ensure your `.env` file has restricted permissions: `chmod 600 .env`
- Regularly update Docker images with `docker-compose pull` followed by a restart
- Review Nginx logs for suspicious activity
- Consider implementing rate limiting for authentication endpoints
- For production, restrict direct access to Apache by configuring your firewall

## 🔄 Maintenance Tasks

### Restarting Services

```bash
# Restart a specific service
docker-compose restart nginx

# Restart the entire stack
docker-compose down && docker-compose up -d
```

### Updating Configurations

After modifying Nginx configuration files:

```bash
# Test the configuration
docker-compose exec nginx nginx -t

# Reload Nginx if the test is successful
docker-compose exec nginx nginx -s reload
```

### Backing Up Data

Create backups of important data:

```bash
# Back up Docker volumes
docker run --rm -v apache-stack_svn_repos:/source:ro -v $(pwd)/backups:/backup \
  -w /source busybox tar -czf /backup/svn_repos_$(date +%Y%m%d).tar.gz .

docker run --rm -v apache-stack_git_repos:/source:ro -v $(pwd)/backups:/backup \
  -w /source busybox tar -czf /backup/git_repos_$(date +%Y%m%d).tar.gz .

# Back up MySQL databases
docker-compose exec mysql sh -c 'mysqldump -u root -p"$MYSQL_ROOT_PASSWORD" --all-databases' > backups/all_databases_$(date +%Y%m%d).sql
```

## 🚀 Next Steps

- [ ] Configure automatic Nginx reload when certificates are renewed
- [ ] Implement rate limiting for sensitive endpoints
- [ ] Add monitoring and alerting for service health
- [ ] Configure HTTP/3 (QUIC) for even better performance
- [ ] Implement Web Application Firewall (WAF) rules

---

Maintained by **@ranemstsage**