FROM debian:bookworm-slim

# Install SSH server, client, Git, and LDAP tools
RUN apt-get update && apt-get install -y \
    openssh-server \
    python3 \
    python3-pip \
    python3-ldap \
    ldap-utils \
    git git-lfs \
    vim \
    neovim \
    netcat-openbsd \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python MySQL connector and requests via pip
RUN pip3 install mysql-connector-python requests --break-system-packages

# Build and install Subversion 1.14.5 (same as Redmine)
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        build-essential \
        libserf-dev \
        libapr1-dev \
        libaprutil1-dev \
        libsqlite3-dev \
        zlib1g-dev \
        libssl-dev \
        libutf8proc-dev \
        pkg-config \
        wget \
    ; \
    rm -rf /var/lib/apt/lists/*; \
    cd /tmp; \
    wget https://archive.apache.org/dist/subversion/subversion-1.14.5.tar.bz2; \
    tar -xjf subversion-1.14.5.tar.bz2; \
    cd subversion-1.14.5; \
    ./configure \
        --prefix=/usr/local \
        --with-serf \
        --with-utf8proc=internal \
        --with-lz4=internal \
    ; \
    make; \
    make install; \
    # Clean up build artifacts
    cd /tmp; \
    rm -rf subversion-1.14.5; \
    rm subversion-1.14.5.tar.bz2; \
    # Create necessary symlinks
    ln -sf /usr/local/bin/svn /usr/bin/svn; \
    ln -sf /usr/local/bin/svnadmin /usr/bin/svnadmin; \
    ln -sf /usr/local/bin/svnlook /usr/bin/svnlook; \
    ln -sf /usr/local/bin/svnserve /usr/bin/svnserve; \
    # Update ldconfig to include the new libraries
    echo "/usr/local/lib" > /etc/ld.so.conf.d/local.conf; \
    ldconfig; \
    # Remove build dependencies to keep image size down
    apt-get purge -y --auto-remove build-essential wget pkg-config; \
    apt-get clean

# Create shared group for repositories with specific GID (must match other containers)
RUN groupadd -g 1002 apache-stack

# Ensure daemon user exists and add to apache-stack group
RUN useradd -u 1 -g 1 daemon 2>/dev/null || true && \
    usermod -a -G apache-stack daemon

# Configure Git to trust all repository directories
RUN git config --system --add safe.directory '*'

# Configure Git LFS globally
RUN git lfs install --system

# Create Git LFS storage directory
RUN mkdir -p /usr/local/git-lfs-storage && \
    chown -R daemon:apache-stack /usr/local/git-lfs-storage && \
    chmod -R 775 /usr/local/git-lfs-storage && \
    find /usr/local/git-lfs-storage -type d -exec chmod g+s {} \;

# Create SSH directories
RUN mkdir -p /var/run/sshd /etc/ssh/keys

# Copy configuration and scripts
COPY sshd_config /etc/ssh/sshd_config
COPY scripts/ /opt/scripts/
COPY entrypoint.sh /entrypoint.sh

# Fix line endings and set permissions
RUN sed -i 's/\r$//' /entrypoint.sh && \
    sed -i 's/\r$//' /opt/scripts/*.py && \
    chmod +x /opt/scripts/*.py /entrypoint.sh

# Generate host keys
RUN ssh-keygen -A

# Create log directory and set permissions
RUN mkdir -p /var/log && \
    chmod 755 /var/log && \
    touch /var/log/svn_proxy.log /var/log/git_proxy.log && \
    chmod 666 /var/log/svn_proxy.log /var/log/git_proxy.log

# Expose SSH port
EXPOSE 22

# Use entrypoint to create user dynamically
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/sbin/sshd", "-D"]