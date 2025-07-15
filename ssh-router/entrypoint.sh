#!/bin/bash
# SSH Router Entrypoint - Creates user dynamically from environment variables

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
else
    echo "User $ADMIN_USERNAME already exists"
fi

# Update SSH config to use the dynamic username
sed -i "s/ADMIN_USERNAME_PLACEHOLDER/$ADMIN_USERNAME/g" /etc/ssh/sshd_config

# Set up authorized keys file path
KEYS_FILE="/etc/ssh/keys/${ADMIN_USERNAME}_authorized_keys"
echo "SSH keys file: $KEYS_FILE"

# Create keys directory if it doesn't exist
mkdir -p /etc/ssh/keys

# Make sure the keys file exists (even if empty)
touch "$KEYS_FILE"
chmod 600 "$KEYS_FILE"

# Debug: Show what's in the authorized_keys file
echo "Authorized keys content:"
cat "$KEYS_FILE" | while read line; do
    if [ ! -z "$line" ]; then
        echo "  - $(echo $line | cut -d' ' -f3-)"
    fi
done

# Write environment variables to a file that the scripts can read
echo "Writing environment variables for SSH sessions..."
cat > /etc/ssh/ssh-router-env << EOF
export WINDOWS_USERNAME="${WINDOWS_USERNAME}"
export WINDOWS_HOST="${WINDOWS_HOST:-host.docker.internal}"
export WINDOWS_SSH_PORT="${WINDOWS_SSH_PORT:-2221}"
EOF
chmod 644 /etc/ssh/ssh-router-env

# Start rsyslog for logging
service rsyslog start

echo "SSH Router starting with admin user: $ADMIN_USERNAME"
echo "Logs will be sent to stderr and captured by Docker"

# Execute the main command (sshd with error logging to stderr)
exec "$@"