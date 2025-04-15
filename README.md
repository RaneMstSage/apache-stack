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
- 🧱 Full control over modules (compiled via `--enable-*` flags)

---

## 🛡️ Initial Setup (One-Time Bootstrap)

On first use, run a temporary container to extract Apache’s default `conf` and `htdocs` for local editing:

### 1. **Uncomment the `apache-init` service** in `docker-compose.yml`
### 2. Run:
```bash
docker compose up --build
```

Or use this one-liner:
```bash
docker compose up -d ; sleep 10 ; docker compose down
```

### 3. Fix permissions (on Linux/WSL):
```bash
sudo chmod -R a+rwx ./data
```

### 4. Edit config:
- Open `data/conf/httpd.conf`
- Set `ServerName localhost`

### 5. **Comment out the `apache-init` service**
### 6. Start Apache normally:
```bash
docker compose up -d
```

---

## 📂 Directory Layout

```
apache-stack/
├── apache/                 # Dockerfile and source build context
├── data/
│   ├── conf/               # Mounted to /usr/local/apache2/conf
│   └── htdocs/             # Mounted to /usr/local/apache2/htdocs
├── docker-compose.yml
└── .gitignore
```

---

## 🧪 Test Your Stack

Once the container is running, visit:

- `http://localhost:8080/index.html` — Static HTML/CSS/JS test
- `http://localhost:8080/lua/info` — mod_lua test (see `luainfo.lua`)
- `curl -T test.txt http://localhost:8080/webdav/test.txt` — WebDAV upload test

Make sure:
- `/data/htdocs/webdav` exists and is writable (`chmod 777` or `chown daemon:daemon && chmod 775`)
- `DavLockDB` is defined and points to a writable path (e.g. `/usr/local/apache2/var/DavLock`)
- The following directory exists and is writable:
  ```bash
  mkdir -p ~/docker-volumes/apache-stack/htdocs/webdav
  sudo chown -R daemon:daemon ~/docker-volumes/apache-stack/htdocs/webdav
  chmod -R 775 ~/docker-volumes/apache-stack/htdocs/webdav
  ```

---

## 📝 Notes

- To enable `mod_lua`, ensure the following is in your `httpd.conf`:
  ```apache
  LoadModule lua_module modules/mod_lua.so
  <IfModule lua_module>
      LuaMapHandler "/lua/info" "/usr/local/apache2/htdocs/lua-info.lua"
  </IfModule>
  ```
- To enable WebDAV support, ensure:
  - Modules are loaded: `mod_dav`, `mod_dav_fs`, `mod_dav_lock`
  - You have this in `httpd.conf`:
    ```apache
    DavLockDB "/usr/local/apache2/var/DavLock"

    <Directory "/usr/local/apache2/htdocs/webdav">
        Dav On
        Options Indexes
        AllowOverride None
        Require all granted
    </Directory>
    ```

- If Apache exits or logs `AH00526`, check for missing modules like `mod_auth_digest`.
- If WebDAV fails with 500, it’s almost always a permissions or `DavLockDB` path issue.
- Logs:
  ```bash
  # To get real Apache errors inside the container:
  docker exec -it apache cat /usr/local/apache2/logs/error_log
  ```

---

## ✅ Next Steps

- [ ] Add PHP-FPM via sidecar container (with mod_proxy_fcgi)
- [ ] Add SVN via mod_dav_svn + Redmine integration
- [ ] Optionally add Digest or Basic auth to DAV

---

Maintained by **@ranemstsage**