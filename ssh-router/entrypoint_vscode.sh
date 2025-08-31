#!/bin/bash
# SSH Router Entrypoint - VS Code Compatible Version
set -e

# Get admin username from environment (no default - must be provided)
ADMIN_USERNAME=${ADMIN_USERNAME}
if [ -z "$ADMIN_USERNAME" ]; then
    echo "Error: ADMIN_USERNAME environment variable required"
    exit 1
fi

# Ensure scripts are executable before creating users
chmod +x /opt/scripts/*.py 2>/dev/null || true
chmod +x /opt/scripts/*.sh 2>/dev/null || true
chmod +x /opt/scripts/admin_shell.sh /opt/scripts/windows_proxy_smart.py

echo "Creating SSH user: $ADMIN_USERNAME"
# Create the admin user if it doesn't exist
if ! id "$ADMIN_USERNAME" &>/dev/null; then
    useradd -m -s /opt/scripts/admin_shell.sh "$ADMIN_USERNAME"
    echo "Created user: $ADMIN_USERNAME with smart shell"

    # Unlock the account (important for SSH key-only auth)
    usermod -p '*' "$ADMIN_USERNAME"
    echo "Unlocked user account"
else
    echo "User $ADMIN_USERNAME already exists"
    # Update shell to smart shell
    usermod -s /opt/scripts/admin_shell.sh "$ADMIN_USERNAME"
fi

# Create git user for repository access
GIT_USERNAME=${GIT_USERNAME:-git}
echo "Creating git user: $GIT_USERNAME"
if ! id "$GIT_USERNAME" &>/dev/null; then
    useradd -m -s /bin/bash "$GIT_USERNAME"
    echo "Created user: $GIT_USERNAME"

    # Unlock the account (important for SSH key-only auth)
    usermod -p '*' "$GIT_USERNAME"
    echo "Unlocked user account"
    
    # Configure Git to trust all repositories
    su - ${GIT_USERNAME} -c "git config --global --add safe.directory '*'"
    echo "Configured Git safe directories"
else
    echo "User $GIT_USERNAME already exists"
    # Still configure git in case the container was recreated
    su - ${GIT_USERNAME} -c "git config --global --add safe.directory '*'"
    echo "Configured Git safe directories"
fi

# Create SVN user for repository access
SVN_USERNAME=${SVN_USERNAME:-svn}
echo "Creating SVN user: $SVN_USERNAME"
if ! id "$SVN_USERNAME" &>/dev/null; then
    useradd -m -s /bin/bash "$SVN_USERNAME"
    echo "Created user: $SVN_USERNAME"

    # Unlock the account (important for SSH key-only auth)
    usermod -p '*' "$SVN_USERNAME"
    echo "Unlocked user account"
else
    echo "User $SVN_USERNAME already exists"
fi

# Use VS Code compatible SSH config
cp /etc/ssh/sshd_config_vscode /etc/ssh/sshd_config

# Update SSH config to use the dynamic usernames
sed -i "s/ADMIN_USERNAME_PLACEHOLDER/$ADMIN_USERNAME/g" /etc/ssh/sshd_config
sed -i "s/GIT_USERNAME_PLACEHOLDER/$GIT_USERNAME/g" /etc/ssh/sshd_config
sed -i "s/SVN_USERNAME_PLACEHOLDER/$SVN_USERNAME/g" /etc/ssh/sshd_config

# Set up authorized keys file path for admin user ONLY
KEYS_FILE="/etc/ssh/keys/${ADMIN_USERNAME}_authorized_keys"
echo "Admin SSH keys file: $KEYS_FILE"

# Create keys directory if it doesn't exist
mkdir -p /etc/ssh/keys
chown root:root /etc/ssh/keys
chmod 755 /etc/ssh/keys

# Make sure the admin keys file exists (even if empty)
touch "$KEYS_FILE"
chmod 600 "$KEYS_FILE"
chown ${ADMIN_USERNAME}:${ADMIN_USERNAME} "$KEYS_FILE"

# Make scripts executable (ensure admin_shell.sh is executable)
chmod +x /opt/scripts/*.py 2>/dev/null || true
chmod +x /opt/scripts/*.sh 2>/dev/null || true
chmod +x /opt/scripts/admin_shell.sh /opt/scripts/windows_proxy_smart.py

echo "Git and SVN users will use database authentication for SSH keys"

# Write environment variables to a file that the scripts can read
echo "Writing environment variables for SSH sessions..."
cat > /etc/ssh/ssh-router-env << EOF
export ADMIN_USERNAME="${ADMIN_USERNAME}"
export GIT_USERNAME="${GIT_USERNAME}"
export SVN_USERNAME="${SVN_USERNAME}"
export WINDOWS_SSH_HOST="${WINDOWS_SSH_HOST:-host.docker.internal}"
export WINDOWS_SSH_PORT="${WINDOWS_SSH_PORT:-2221}"
export GIT_REPOS_PATH="${GIT_REPOS_PATH:-/opt/repositories/git}"
export SVN_REPOS_PATH="${SVN_REPOS_PATH:-/opt/repositories/svn}"
export LDAP_HOST="${LDAP_HOST:-openldap}"
export LDAP_PORT="${LDAP_PORT:-389}"
export LDAP_BASE_DN="${LDAP_BASE_DN:-dc=mstsage,dc=com}"
export LDAP_BIND_DN="${LDAP_BIND_DN:-cn=admin,dc=mstsage,dc=com}"
export LDAP_BIND_PASSWORD="${LDAP_BIND_PASSWORD}"
export MYSQL_HOST="${MYSQL_HOST:-mysql}"
export MYSQL_DATABASE="${MYSQL_DATABASE}"
export MYSQL_USER="${MYSQL_USER}"
export MYSQL_PASSWORD="${MYSQL_PASSWORD}"
export MYSQL_PORT="${MYSQL_PORT:-3306}"
export USE_DATABASE_AUTH="${USE_DATABASE_AUTH:-true}"
EOF
chmod 644 /etc/ssh/ssh-router-env

# Ensure apache-stack group exists with correct GID
if ! getent group apache-stack > /dev/null 2>&1; then
    groupadd -g 1002 apache-stack
    echo "Created apache-stack group with GID 1002"
fi

# Add all SSH users to apache-stack group for repository access
usermod -a -G apache-stack "$ADMIN_USERNAME"
echo "Added $ADMIN_USERNAME to apache-stack group"

usermod -a -G apache-stack "$GIT_USERNAME"
echo "Added $GIT_USERNAME to apache-stack group"

usermod -a -G apache-stack "$SVN_USERNAME"
echo "Added $SVN_USERNAME to apache-stack group"

# Install VS Code dependencies if not present
if ! command -v curl &> /dev/null; then
    apt-get update && apt-get install -y curl wget
    echo "Installed curl and wget for VS Code"
fi

echo "=========================================="
echo "SSH Router (VS Code Compatible) Starting"
echo "=========================================="
echo "Admin user: $ADMIN_USERNAME"
echo "Git user: $GIT_USERNAME"
echo "SVN user: $SVN_USERNAME"
echo "VS Code Remote SSH: Enabled"
echo "=========================================="

# Execute the main command
exec "$@"