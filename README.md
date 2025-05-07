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
- ✅ Full Subversion 1.14.5 integration with all language bindings (Python, Perl, Ruby, Java)
- ✅ Git integration with HTTP backend for repository access
- 🧱 Full control over modules (compiled via `--enable-*` flags)

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
├── docker-volumes/         # Host directory bind mounts
│   ├── conf/               # Mounted to /usr/local/apache2/conf
│   ├── htdocs/             # Mounted to /usr/local/apache2/htdocs
│   ├── uploads/            # Mounted to /usr/local/apache2/uploads (DAV)
│   ├── var/                # Mounted to /usr/local/apache2/var (for DavLockDB)
│   └── user.passwd         # Auth file for SVN and Git
├── docker-compose.yml      # Defines services and volumes
└── .gitignore
```

## Docker Volumes
```
svn_repos               # Docker volume for SVN repositories
git_repos               # Docker volume for Git repositories
```

The SVN and Git repositories are stored in Docker volumes for better performance, especially when running in WSL environments. These volumes are managed by Docker rather than being bind-mounted from the host filesystem.

---

## 🧪 Test Your Stack
Once the container is running, visit:
- `http://localhost:8080/index.html` — Static HTML/CSS/JS test
- `http://localhost:8080/lua/info` — mod_lua test (see `luainfo.lua`)
- `http://localhost:8080/svn` — Subversion repository browser
- `http://localhost:8080/git` — Git repositories access
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

### Subversion Configuration
- Create `conf/extra/httpd-svn.conf` with:
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
- Include this file in your `httpd.conf`:
  ```apache
  # Subversion configuration
  Include conf/extra/httpd-svn.conf
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

### Git Configuration
- Create `conf/extra/httpd-git.conf` with:
  ```apache
  # Git configuration
  <Directory "/usr/local/apache2/git">
      Options None
      AllowOverride None
      Require all granted
  </Directory>

  # Set environment variables for Git
  SetEnv GIT_PROJECT_ROOT /usr/local/apache2/git
  SetEnv GIT_HTTP_EXPORT_ALL

  # Configure the Git HTTP backend
  ScriptAlias /git/ /usr/local/apache2/cgi-bin/git-http-backend/

  # Add authentication for Git operations
  <LocationMatch "^/git/(.*/)?(.+\.git)/(git-(upload|receive)-pack)$">
      AuthType Basic
      AuthName "Git Repository"
      AuthUserFile /usr/local/apache2/user.passwd
      Require valid-user
  </LocationMatch>
  ```
- Include this file in your `httpd.conf`:
  ```apache
  # Git configuration
  Include conf/extra/httpd-git.conf
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

### Lua Configuration
- To enable `mod_lua`, ensure:
  ```apache
  LoadModule lua_module modules/mod_lua.so
  <IfModule lua_module>
      LuaMapHandler "/lua/info" "/usr/local/apache2/htdocs/lua-info.lua"
  </IfModule>
  ```

### Checking Logs
- Apache logs (real error logs):
  ```bash
  docker exec -it apache cat /usr/local/apache2/logs/error_log
  ```

---

## ✅ Next Steps
- [x] Add PHP-FPM via sidecar container (with mod_proxy_fcgi) ✓ (Already implemented)
- [x] Add SVN via mod_dav_svn
- [x] Add Git integration via HTTP backend
- [ ] Add Redmine integration
- [ ] Replace Basic auth with LDAP-backed auth

---

Maintained by **@ranemstsage**