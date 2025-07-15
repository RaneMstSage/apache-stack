#!/bin/bash
# Debug script for SSH Router - Configuration check only

echo "=== SSH Router Debug Information ==="
echo

echo "1. User information:"
echo "   Username: sage"
echo "   User exists: $(id sage >/dev/null 2>&1 && echo 'YES' || echo 'NO')"
echo "   Home directory: $(getent passwd sage | cut -d: -f6)"

echo
echo "2. Authorized keys file:"
KEYS_FILE="/etc/ssh/keys/sage_authorized_keys"
if [ -f "$KEYS_FILE" ]; then
    echo "   File exists: YES"
    echo "   Permissions: $(stat -c %a $KEYS_FILE)"
    echo "   Owner: $(stat -c %U:%G $KEYS_FILE)"
    echo "   Size: $(stat -c %s $KEYS_FILE) bytes"
    echo "   Lines: $(wc -l < $KEYS_FILE)"
else
    echo "   File exists: NO"
fi

echo
echo "3. Key fingerprints in authorized_keys:"
if [ -f "$KEYS_FILE" ]; then
    ssh-keygen -lf $KEYS_FILE 2>/dev/null || echo "   Error reading keys"
fi

echo
echo "4. SSH daemon configuration:"
echo "   Config file: /etc/ssh/sshd_config"
echo "   Port: $(grep '^Port' /etc/ssh/sshd_config | awk '{print $2}')"
echo "   PubkeyAuthentication: $(grep '^PubkeyAuthentication' /etc/ssh/sshd_config | awk '{print $2}')"
echo "   PasswordAuthentication: $(grep '^PasswordAuthentication' /etc/ssh/sshd_config | awk '{print $2}')"
echo "   LogLevel: $(grep '^LogLevel' /etc/ssh/sshd_config | awk '{print $2}')"

echo
echo "5. Match block for sage user:"
awk '/Match User sage/,/^$|^Match/' /etc/ssh/sshd_config | grep -v '^$'

echo
echo "6. Environment variables:"
if [ -f /etc/ssh/ssh-router-env ]; then
    cat /etc/ssh/ssh-router-env | sed 's/=.*/=<hidden>/'
else
    echo "   Environment file not found"
fi

echo
echo "7. SSH process status:"
ps aux | grep sshd | grep -v grep

echo
echo "=== End Debug Information ==="