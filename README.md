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
├── docker-volumes/
│   ├── conf/               # Mounted to /usr/local/apache2/conf
│   ├── htdocs/             # Mounted to /usr/local/apache2/htdocs
│   ├── uploads/            # Mounted to /usr/local/apache2/uploads (DAV)
│   ├── var/                # Mounted to /usr/local/apache2/var (for DavLockDB)
│   └── user.passwd         # Digest auth file
├── docker-compose.yml
└── .gitignore
```

---

## 🧪 Test Your Stack

Once the container is running, visit:

- `http://localhost:8080/index.html` — Static HTML/CSS/JS test
- `http://localhost:8080/lua/info` — mod_lua test (see `luainfo.lua`)
- `curl --digest -u admin:yourpassword -T test.txt http://localhost:8080/uploads/test.txt` — WebDAV upload test (with auth)

Ensure these directories exist and are writable:
```bash
mkdir -p ~/docker-volumes/apache-stack/htdocs/webdav
mkdir -p ~/docker-volumes/apache-stack/uploads
mkdir -p ~/docker-volumes/apache-stack/var

sudo chown -R daemon:daemon ~/docker-volumes/apache-stack/uploads
sudo chown -R daemon:daemon ~/docker-volumes/apache-stack/var
chmod -R 775 ~/docker-volumes/apache-stack/uploads
chmod -R 775 ~/docker-volumes/apache-stack/var
```

To create your DAV password file:
```bash
htdigest -c ~/docker-volumes/apache-stack/user.passwd DAV-upload admin
```

---

## 📝 Notes

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

- To enable `mod_lua`, ensure:
  ```apache
  LoadModule lua_module modules/mod_lua.so
  <IfModule lua_module>
      LuaMapHandler "/lua/info" "/usr/local/apache2/htdocs/lua-info.lua"
  </IfModule>
  ```

- Apache logs (real error logs):
  ```bash
  docker exec -it apache cat /usr/local/apache2/logs/error_log
  ```

---

## ✅ Next Steps

- [ ] Add PHP-FPM via sidecar container (with mod_proxy_fcgi)
- [ ] Add SVN via mod_dav_svn + Redmine integration
- [ ] Replace Digest auth with LDAP-backed auth

---

Maintained by **@ranemstsage**