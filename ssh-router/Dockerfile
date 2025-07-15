FROM debian:bookworm-slim

# Install SSH server, client, Git, and LDAP tools
RUN apt-get update && apt-get install -y \
    openssh-server \
    openssh-client \
    python3 \
    git \
    python3-ldap3 \
    ldap-utils \
    && rm -rf /var/lib/apt/lists/*

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