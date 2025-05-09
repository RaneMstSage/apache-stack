# Apache Stack: Build from Source using Docker

This repository builds Apache HTTPD 2.4.63 from source using a Dockerfile based on a clean Debian image. It mirrors the build process described [here](https://www.apachelounge.com/viewtopic.php?t=8609) (originally Windows-focused), adapted for full Linux containerization with extensible module control.

---

## 🔧 Requirements
- Docker
- Docker Compose v2+

---

## 📆 Stack Features
- ✅ Apache HTTPD built 100% from source
- ✅ mod_fcgid built separately from source
- ✅ HTTP/2, Brotli, SSL (OpenSSL 3.x), DAV, Lua
- ✅ WebDAV support with configurable `DavLockDB`
- ✅ mod_lua with `LuaMapHandler` working
- ✅ Python integration via mod_wsgi with virtual environment
- ✅ Full Subversion 1.14.5 integration with all language bindings (Python, Perl, Ruby, Java)
- ✅ Git integration with HTTP backend for repository access
- ✅ PHP 8.2-FPM with optimized extensions
- ✅ MySQL 8.0 database with persistent storage
- ✅ Redmine 6.0.5 with custom SageDark theme
- 🧱 Full control over modules (compiled via `--enable-*` flags)

---

## 🎨 SageDark Theme
Our custom dark theme for Redmine provides a comprehensive dark mode experience:

### Features
- Dark background with amber/gold accents, now using #116699 for links
- Enhanced styling for Scrum/Agile plugin with proper spacing between menu icons
- Custom styling for NVD3 and XChart visualizations
- Post-it notes with appropriate contrast in dark mode
- Consistent color scheme throughout the interface

The theme provides better readability in low-light environments while maintaining professional aesthetics.

---

## 🛡️ Setup
On first use, copy in default `conf` and `htdocs` folders or use pre-distributed versions.

If you still want to bootstrap with Apache's defaults:

### (Optional) Apache Init Workflow:
Uncomment the `apache-init` block in `docker-compose.yml` and run:
```bash
docker compose up -d ; sleep 10 ; docker compose down
```

Then fix permissions:
```bash
sudo chmod -R a+rwx ~/docker-volumes/apache-stack
```

Edit `conf/httpd.conf`:
- Set `ServerName localhost`

Re-comment `apache-init`, then start:
```bash
docker compose up -d
```

---

## 📂 Directory Layout
```
apache-stack/
├── apache/                 # Dockerfile and source build context
├── php/                    # PHP-FPM Dockerfile and configuration
├── redmine/                # Redmine Dockerfile and customizations
├── docker-volumes/         # Host directory bind mounts
│   ├── conf/               # Mounted to /usr/local/apache2/conf
│   │   └── extra/          # Additional configuration files
│   │       ├── httpd-git.conf       # Git integration
│   │       ├── httpd-lua.conf       # Lua configuration
│   │       ├── httpd-php-fcgi.conf  # PHP-FPM integration
│   │       ├── httpd-python.conf    # Python WSGI integration
│   │       └── httpd-svn.conf       # Subversion integration
│   ├── htdocs/             # Mounted to /usr/local/apache2/htdocs
│   ├── uploads/            # Mounted to /usr/local/apache2/uploads (DAV)
│   ├── var/                # Mounted to /usr/local/apache2/var (for DavLockDB)
│   ├── python-apps/        # Mounted to /usr/local/apache2/python-apps
│   ├── php/                # PHP configuration files
│   ├── redmine/            # Redmine files and themes
│   │   ├── files/          # Redmine file attachments
│   │   ├── plugins/        # Redmine plugins (incl. Scrum/Agile)
│   │   ├── config/         # Redmine configuration
│   │   └── themes/         # Redmine themes (incl. SageDark)
│   └── user.passwd         # Auth file for SVN and Git
├── docker-compose.yml      # Defines services and volumes
└── .gitignore
```

## Docker Volumes
```
svn_repos               # Docker volume for SVN repositories
git_repos               # Docker volume for Git repositories
mysql_data              # Docker volume for MySQL data
```

The SVN and Git repositories are stored in Docker volumes for better performance, especially when running in WSL environments. These volumes are managed by Docker rather than being bind-mounted from the host filesystem.

---

## 🧪 Test Your Stack
Once the container is running, visit:
- `http://localhost:8080/index.html` — Static HTML/CSS/JS test
- `http://localhost:8080/lua/info` — mod_lua test (see `luainfo.lua`)
- `http://localhost:8080/python` — Python WSGI application test
- `http://localhost:8080/svn` — Subversion repository browser
- `http://localhost:8080/git` — Git repositories access
- `http://localhost:3000/` — Redmine with SageDark theme
- `http://localhost:3001/` — Secondary Redmine 5.1 instance
- `curl --digest -u admin:yourpassword -T test.txt http://localhost:8080/uploads/test.txt` — WebDAV upload test (with auth)

Ensure these directories exist and are writable:
```bash
# For WebDAV - just ensure correct permissions
sudo chown -R daemon:daemon ~/docker-volumes/apache-stack/uploads
sudo chown -R daemon:daemon ~/docker-volumes/apache-stack/var
chmod -R 775 ~/docker-volumes/apache-stack/uploads
chmod -R 775 ~/docker-volumes/apache-stack/var
```

To create your auth password file:
```bash
# For basic authentication (SVN and Git)
htpasswd -c ~/docker-volumes/apache-stack/user.passwd username

# For digest authentication (WebDAV)
htdigest -c ~/docker-volumes/apache-stack/user.passwd DAV-upload admin
```

---

## 📝 Notes

### WebDAV Configuration
- Apache must load the following modules:
  ```apache
  LoadModule dav_module modules/mod_dav.so
  LoadModule dav_fs_module modules/mod_dav_fs.so
  LoadModule dav_lock_module modules/mod_dav_lock.so
  LoadModule auth_digest_module modules/mod_auth_digest.so
  ```
- Sample config for DAV + digest auth:
  ```apache
  DavLockDB "/usr/local/apache2/var/DavLock"
  Alias /uploads "/usr/local/apache2/uploads"
  <Directory "/usr/local/apache2/uploads">
      Dav On
      AuthType Digest
      AuthName "DAV-upload"
      AuthUserFile "/usr/local/apache2/user.passwd"
      AuthDigestProvider file
      <RequireAny>
          Require method GET POST OPTIONS
          Require user admin
      </RequireAny>
  </Directory>
  ```

### MySQL Configuration
The stack includes a MySQL 8.0 database server with the following features:
- Persistent data storage via Docker volume
- Environment variable configuration for security
- Separate databases for multiple Redmine instances
- Shared network with Apache and PHP services

```yaml
mysql:
  container_name: mysql
  image: mysql:8.0
  volumes:
    - mysql_data:/var/lib/mysql
  environment:
    MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
    MYSQL_DATABASE: ${MYSQL_DATABASE}
    MYSQL_USER: ${MYSQL_USER}
    MYSQL_PASSWORD: ${MYSQL_PASSWORD}
  ports:
    - "3306:3306"
  networks:
    - apache-network
```

To connect to the MySQL database:
```bash
docker exec -it mysql mysql -u root -p
```

### PHP Configuration
The PHP container uses PHP 8.2-FPM with the following optimizations:
```Dockerfile
FROM php:8.2-fpm

# Install common PHP extensions
RUN apt-get update && apt-get install -y \
        libfreetype6-dev \
        libjpeg62-turbo-dev \
        libpng-dev \
        libzip-dev \
        libxml2-dev \
        libonig-dev \
    && docker-php-ext-install -j$(nproc) \
        gd \
        mysqli \
        pdo_mysql \
        zip \
        opcache \
        mbstring \
        xml

# Set recommended PHP.ini settings
RUN { \
        echo 'opcache.memory_consumption=128'; \
        echo 'opcache.interned_strings_buffer=8'; \
        echo 'opcache.max_accelerated_files=4000'; \
        echo 'opcache.revalidate_freq=2'; \
        echo 'opcache.fast_shutdown=1'; \
        echo 'opcache.enable_cli=1'; \
    } > /usr/local/etc/php/conf.d/opcache-recommended.ini

WORKDIR /var/www/html
```

To integrate PHP with Apache, we use this configuration (`conf/extra/httpd-php-fcgi.conf`):
```apache
# Enable PHP file handling via FPM/FastCGI
<FilesMatch \.php$>
    SetHandler "proxy:fcgi://php:9000"
</FilesMatch>

# Set up .php file support
<IfModule dir_module>
    DirectoryIndex index.php index.html
</IfModule>

# Application settings
AddType application/x-httpd-php .php
AddType application/x-httpd-php-source .phps
```

### Python WSGI Configuration
The stack includes mod_wsgi for running Python applications. The configuration (`conf/extra/httpd-python.conf`):
```apache
# Python WSGI Configuration
LoadModule wsgi_module modules/mod_wsgi.so

<IfModule wsgi_module>
    # Point to the virtual environment instead of system Python
    WSGIPythonHome /usr/local/apache2/python-env
    WSGIPythonPath /usr/local/apache2/python-apps
    
    <Directory /usr/local/apache2/python-apps>
        Options ExecCGI
        Require all granted
    </Directory>

    WSGIScriptAlias /python /usr/local/apache2/python-apps/app.wsgi
</IfModule>
```

### Lua Configuration
To enable `mod_lua`, we use this configuration (`conf/extra/httpd-lua.conf`):
```apache
<IfModule lua_module>
    # Map /lua/info to our lua-info.lua script
    LuaMapHandler "/lua/info" "/usr/local/apache2/htdocs/lua-info.lua"
</IfModule>
```

### Subversion Configuration
Our SVN integration uses this configuration (`conf/extra/httpd-svn.conf`):
```apache
# Load Subversion modules
LoadModule dav_module modules/mod_dav.so
LoadModule dav_fs_module modules/mod_dav_fs.so
LoadModule dav_svn_module modules/mod_dav_svn.so
LoadModule authz_svn_module modules/mod_authz_svn.so

# Repository configuration
<Location /svn>
    DAV svn
    SVNParentPath /usr/local/apache2/svn
    SVNListParentPath On
    
    # Authentication settings
    AuthType Basic
    AuthName "Subversion Repository"
    AuthUserFile /usr/local/apache2/user.passwd
    Require valid-user
</Location>
```

### Git Configuration
Our Git integration uses this configuration (`conf/extra/httpd-git.conf`):
```apache
# Set up Git environment
SetEnv GIT_PROJECT_ROOT /usr/local/apache2/git
SetEnv GIT_HTTP_EXPORT_ALL

# Map /git/ to the Git HTTP backend
ScriptAlias /git/ /usr/local/apache2/cgi-bin/git-http-backend/

<Directory "/usr/local/apache2/cgi-bin">
    # Permit CGI execution
    Options +ExecCGI
    Require all granted
    # For Linux, we need a different handler since there's no .exe
    AddHandler cgi-script .cgi
</Directory>

<Location /git>
    # Basic auth
    AuthType Basic
    AuthName "Git Repository"
    AuthUserFile /usr/local/apache2/user.passwd
    Require valid-user
</Location>
```

### Creating Subversion Repositories
To create a Subversion repository:
```bash
docker exec -it apache svnadmin create /usr/local/apache2/svn/testrepo
docker exec -it apache chown -R daemon:daemon /usr/local/apache2/svn/testrepo
```

To checkout and use the repository:
```bash
svn checkout http://localhost:8080/svn/testrepo --username username
cd testrepo
echo "Test file" > testfile.txt
svn add testfile.txt
svn commit -m "Initial commit" --username username
```

### Creating Git Repositories
To create a Git repository:
```bash
# Create a bare Git repository
docker exec -it apache bash -c "mkdir -p /usr/local/apache2/git/myrepo.git && cd /usr/local/apache2/git/myrepo.git && git init --bare && chown -R daemon:daemon /usr/local/apache2/git/myrepo.git"
```

To clone and use the repository:
```bash
# Clone the repository
git clone http://localhost:8080/git/myrepo.git

# Add content and push
cd myrepo
echo "# My Repository" > README.md
git add README.md
git config user.email "your.email@example.com"
git config user.name "Your Name"
git commit -m "Initial commit"
git push -u origin main
```

Note: Both SVN and Git repositories use the same authentication system, so users created for SVN access can also be used for Git.

### Redmine with SageDark Theme
The Redmine instance is configured with custom styling for better dark mode experience. The SageDark theme includes custom CSS for:
- Main Redmine interface
- Scrum/Agile plugin with properly spaced menu items
- NVD3 charts in dark mode
- XChart visualizations in dark mode

The theme is configured to use #116699 as the link color for better readability against the dark background.

### Checking Logs
- Apache logs (real error logs):
  ```bash
  docker exec -it apache cat /usr/local/apache2/logs/error_log
  ```
- Redmine logs:
  ```bash
  docker exec -it redmine cat /usr/src/redmine/log/production.log
  ```
- MySQL logs:
  ```bash
  docker exec -it mysql bash -c "tail -f /var/log/mysql/error.log"
  ```

---

## ✅ Next Steps
- [x] Add PHP-FPM via sidecar container (with mod_proxy_fcgi)
- [x] Add SVN via mod_dav_svn
- [x] Add Git integration via HTTP backend
- [x] Add Python WSGI integration
- [x] Add Redmine integration with custom SageDark theme
- [x] Add MySQL database for Redmine and future applications
- [ ] Replace Basic auth with LDAP-backed auth
- [ ] Add Nginx reverse proxy configuration

---

Maintained by **@ranemstsage**