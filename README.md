# Apache Stack: Build from Source using Docker

This repository builds Apache HTTPD from source using a Dockerfile based on a clean Debian image. It mirrors the build process described here: https://www.apachelounge.com/viewtopic.php?t=8609 (originally intended for Windows), adapted for Linux in a containerized environment.

## 🔧 Requirements
- Docker
- Docker Compose (v2+)

## 📦 Contents
- `apache/Dockerfile`: Full build from source (Apache, APR, OpenSSL, PCRE, etc.)
- `docker-compose.yml`: Volume mount setup for editable `conf` and `htdocs`
- `data/conf`, `data/htdocs`: Your local Apache configuration and web root

## 🧱 Initial Build Setup
On first use, follow these steps to extract default Apache configuration and htdocs locally:

1. **Uncomment the `apache-init` service** block in `docker-compose.yml`.
2. Run:
   ```bash
   docker compose up --build
   ```
   This copies `/usr/local/apache2/conf` and `/usr/local/apache2/htdocs` to `./data/`.

3. Shut down:
   ```bash
   docker compose down
   ```
   Or in one command:
   ```bash
   docker compose up -d ; sleep 10 ; docker compose down
   ```

4. **Fix permissions** (if needed):
   ```bash
   sudo chmod -R a+rwx ./data
   ```

5. **Edit the following in your local files**:
   - Open `data/conf/httpd.conf`
   - Set a valid `ServerName` (e.g., `ServerName localhost`)

6. **Comment out or delete the `apache-init` block** in `docker-compose.yml`.

7. Now start your Apache container normally:
   ```bash
   docker compose up
   ```

## 🗂️ Directory Layout
```
├── apache/
│   └── Dockerfile           # Full source-based Apache build
├── data/
│   ├── conf/                # Apache config (mounted into container)
│   └── htdocs/              # Web content root (mounted into container)
├── docker-compose.yml
└── .gitignore
```

## 📝 Notes
- `mod_fcgid` is built manually from source.
- You can now edit `conf` and `htdocs` locally and changes are reflected immediately in the container.
- If Apache fails to start, check the logs for `ServerName` or syntax issues.

## ✅ Next Steps
- Add PHP-FPM support (via another container)
- Wire in Subversion + Redmine

---
Maintained by @ranemstsage

