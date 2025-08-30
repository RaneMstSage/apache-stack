#!/bin/bash
# Admin shell wrapper - provides choice between local container or Windows proxy

# Load environment variables
source /etc/ssh/ssh-router-env 2>/dev/null

# Check if SSH_ORIGINAL_COMMAND contains VS Code patterns
if [[ -n "$SSH_ORIGINAL_COMMAND" ]]; then
    # VS Code commands - execute directly in container
    if [[ "$SSH_ORIGINAL_COMMAND" == *"vscode"* ]] || \
       [[ "$SSH_ORIGINAL_COMMAND" == "bash"* ]] || \
       [[ "$SSH_ORIGINAL_COMMAND" == "sh"* ]] || \
       [[ "$SSH_ORIGINAL_COMMAND" == "uname"* ]] || \
       [[ "$SSH_ORIGINAL_COMMAND" == "test"* ]] || \
       [[ "$SSH_ORIGINAL_COMMAND" == "echo"* ]] || \
       [[ "$SSH_ORIGINAL_COMMAND" == "pwd"* ]]; then
        # Execute command directly for VS Code
        exec bash -c "$SSH_ORIGINAL_COMMAND"
    else
        # Other commands - proxy to Windows
        exec /opt/scripts/windows_proxy_smart.py
    fi
fi

# Interactive session - give user a choice
echo "=========================================="
echo "SSH Router - Admin Connection"
echo "=========================================="
echo ""
echo "Where would you like to connect?"
echo "1) Local container shell (for VS Code/debugging)"
echo "2) Windows WSL host (default)"
echo ""
echo -n "Choice [1-2] (default=2): "

# Read with timeout
read -t 10 -n 1 choice
echo ""

case "$choice" in
    1)
        echo "Starting local container shell..."
        exec /bin/bash
        ;;
    *)
        echo "Proxying to Windows WSL host..."
        exec /opt/scripts/windows_proxy_smart.py
        ;;
esac