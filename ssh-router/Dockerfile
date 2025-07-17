FROM debian:bookworm-slim

# Install SSH server, client, Git, and LDAP tools
RUN apt-get update && apt-get install -y \
    openssh-server \
    python3 \
    python3-pip \
    python3-ldap \
    ldap-utils \
    git \
    subversion \
    vim \
    neovim \
    netcat \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create shared groups for repositories with specific GIDs
RUN groupadd -g 1002 gitaccess && \
    groupadd -g 1003 svnaccess

# Ensure daemon user exists and add to both groups
RUN useradd -u 1 -g 1 daemon 2>/dev/null || true && \
    usermod -a -G gitaccess,svnaccess daemon

# Create SSH directories
RUN mkdir -p /var/run/sshd /etc/ssh/keys

# Copy configuration and scripts
COPY sshd_config /etc/ssh/sshd_config
COPY scripts/ /opt/scripts/
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /opt/scripts/*.py /entrypoint.sh

# Generate host keys
RUN ssh-keygen -A

# Expose SSH port
EXPOSE 22

# Use entrypoint to create user dynamically
ENTRYPOINT ["/entrypoint.sh"]
CMD ["/usr/sbin/sshd", "-D"]