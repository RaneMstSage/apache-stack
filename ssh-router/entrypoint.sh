#!/bin/bash
# SSH Router Entrypoint - Creates users dynamically from environment variables
set -e

# Get admin username from environment (no default - must be provided)
ADMIN_USERNAME=${ADMIN_USERNAME}
if [ -z "$ADMIN_USERNAME" ]; then
    echo "Error: ADMIN_USERNAME environment variable required"
    exit 1
fi

echo "Creating SSH user: $ADMIN_USERNAME"
# Create the admin user if it doesn't exist
if ! id "$ADMIN_USERNAME" &>/dev/null; then
    useradd -m -s /bin/bash "$ADMIN_USERNAME"
    echo "Created user: $ADMIN_USERNAME"

    # Unlock the account (important for SSH key-only auth)
    usermod -p '*' "$ADMIN_USERNAME"
    echo "Unlocked user account"
else
    echo "User $ADMIN_USERNAME already exists"
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

# Update SSH config to use the dynamic usernames
sed -i "s/ADMIN_USERNAME_PLACEHOLDER/$ADMIN_USERNAME/g" /etc/ssh/sshd_config
sed -i "s/GIT_USERNAME_PLACEHOLDER/$GIT_USERNAME/g" /etc/ssh/sshd_config
sed -i "s/SVN_USERNAME_PLACEHOLDER/$SVN_USERNAME/g" /etc/ssh/sshd_config

# Set up authorized keys file path for admin user
KEYS_FILE="/etc/ssh/keys/${ADMIN_USERNAME}_authorized_keys"
echo "Admin SSH keys file: $KEYS_FILE"

# Set up authorized keys file path for git user
GIT_KEYS_FILE="/etc/ssh/keys/${GIT_USERNAME}_authorized_keys"
echo "Git SSH keys file: $GIT_KEYS_FILE"

# Set up authorized keys file path for SVN user
SVN_KEYS_FILE="/etc/ssh/keys/${SVN_USERNAME}_authorized_keys"
echo "SVN SSH keys file: $SVN_KEYS_FILE"

# Create keys directory if it doesn't exist
mkdir -p /etc/ssh/keys
chown root:root /etc/ssh/keys
chmod 755 /etc/ssh/keys

# Make sure the admin keys file exists (even if empty)
touch "$KEYS_FILE"
chmod 600 "$KEYS_FILE"
chown ${ADMIN_USERNAME}:${ADMIN_USERNAME} "$KEYS_FILE"

# Make sure the git keys file exists (even if empty)
touch "$GIT_KEYS_FILE"
chmod 600 "$GIT_KEYS_FILE"
chown ${GIT_USERNAME}:${GIT_USERNAME} "$GIT_KEYS_FILE"

# Make sure the SVN keys file exists (even if empty)
touch "$SVN_KEYS_FILE"
chmod 600 "$SVN_KEYS_FILE"
chown ${SVN_USERNAME}:${SVN_USERNAME} "$SVN_KEYS_FILE"

# Write environment variables to a file that the scripts can read
echo "Writing environment variables for SSH sessions..."
cat > /etc/ssh/ssh-router-env << EOF
export ADMIN_USERNAME="${ADMIN_USERNAME}"
export GIT_USERNAME="${GIT_USERNAME}"
export SVN_USERNAME="${SVN_USERNAME}"
export WINDOWS_USERNAME="${WINDOWS_USERNAME}"
export WINDOWS_HOST="${WINDOWS_HOST:-host.docker.internal}"
export WINDOWS_SSH_PORT="${WINDOWS_SSH_PORT:-2221}"
export GIT_REPOS_PATH="${GIT_REPOS_PATH:-/opt/repositories/git}"
export SVN_REPOS_PATH="${SVN_REPOS_PATH:-/opt/repositories/svn}"
export LDAP_HOST="${LDAP_HOST:-openldap}"
export LDAP_PORT="${LDAP_PORT:-389}"
export LDAP_BASE_DN="${LDAP_BASE_DN:-dc=mstsage,dc=com}"
export LDAP_BIND_DN="${LDAP_BIND_DN:-cn=admin,dc=mstsage,dc=com}"
export LDAP_BIND_PASSWORD="${LDAP_BIND_PASSWORD}"
EOF
chmod 644 /etc/ssh/ssh-router-env

echo "SSH router starting with admin user: $ADMIN_USERNAME, git user: $GIT_USERNAME, and svn user: $SVN_USERNAME"

# Execute the main command
exec "$@"