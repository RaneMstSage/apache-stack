#!/usr/bin/env python3
"""
Windows SSH Proxy - Routes admin SSH connections to Windows host
"""
import os
import sys
import subprocess

def proxy_to_windows():
    """Proxy SSH connection to Windows host"""
    
    # Get Windows host details from environment
    windows_host = os.environ.get('WINDOWS_HOST', 'host.docker.internal')
    windows_port = os.environ.get('WINDOWS_SSH_PORT', '2221')
    
    # Get Windows target username (separate from SSH router username)
    windows_username = os.environ.get('WINDOWS_USERNAME')
    if not windows_username:
        print("Error: WINDOWS_USERNAME environment variable required")
        sys.exit(1)
    
    # Get the original SSH command if any
    original_command = os.environ.get('SSH_ORIGINAL_COMMAND', '')
    
    print(f"Routing SSH connection to Windows host: {windows_username}@{windows_host}:{windows_port}")
    
    # Build SSH command to proxy to Windows
    ssh_cmd = [
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-p', windows_port,
        f"{windows_username}@{windows_host}"
    ]
    
    # If there was an original command, pass it through
    if original_command:
        ssh_cmd.append(original_command)
    
    try:
        # Execute the proxy connection
        os.execvp('ssh', ssh_cmd)
    except Exception as e:
        print(f"Error proxying to Windows: {e}")
        sys.exit(1)

if __name__ == "__main__":
    proxy_to_windows()