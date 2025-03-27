# Apache Stack (Docker-based)

This project provides a reproducible, portable Docker-based Apache build from source with support for modules like `mod_fcgid`.

## ⚙️ Initial Setup Instructions

### 1. Build the Apache Docker Image

You must **manually build the image first** before using `docker compose`:

```bash
docker build -t apache ./apache
```

> This step compiles all dependencies and Apache from source. It may take a while on the first run.

---

### 2. Extract Default Config and Web Root

To get a local copy of Apache's config and `htdocs`, you **must uncomment the `apache-init` service** in `docker-compose.yml` temporarily:

```yaml
# apache-init:
#   image: apache
#   command: >
#     bash -c "
#       mkdir -p /mnt/conf /mnt/htdocs &&
#       cp -r /usr/local/apache2/conf/* /mnt/conf 2>/dev/null || true &&
#       cp -r /usr/local/apache2/htdocs/* /mnt/htdocs 2>/dev/null || true"
#   volumes:
#     - ./data/conf:/mnt/conf
#     - ./data/htdocs:/mnt/htdocs
#   entrypoint: ""
```

Then run:

```bash
docker compose up
```

This will copy the default Apache configuration and web content into `./data/conf` and `./data/htdocs`.

Once done, **you can comment out `apache-init` again** and proceed to use only the `apache` service.

---

### 3. Running Apache with Docker Compose

After config/htdocs are extracted, just run:

```bash
docker compose up
```

Apache will run on:
- `http://localhost:8080`
- `https://localhost:8443`

---

### 4. Editing Configuration or Content

- **Apache config:** `./data/conf/httpd.conf` (and other files in `./data/conf`)
- **Web root (htdocs):** `./data/htdocs/`

These are bind-mounted into the container, so you can edit them directly on your host.

---

### 🛉 Clean Up

To remove the temporary `apache-init` container:

```bash
docker compose down --remove-orphans
```

---

### 📌 Notes

- `mod_fcgid` is compiled and enabled.
- PHP and Subversion support coming in future steps.

