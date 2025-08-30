#!/usr/bin/env python3
"""
Smart Windows SSH Proxy - Routes admin SSH connections to Windows host
Supports VS Code Remote SSH by detecting VS Code commands
"""
import os
import sys
import subprocess
import shlex

def load_environment():
    """Load environment variables from file since SSH doesn't pass Docker env vars"""
    env_file = '/etc/ssh/ssh-router-env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('export '):
                    line = line[7:]  # Remove 'export '
                if '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    os.environ[key] = value

def is_vscode_command(command):
    """Check if this is a VS Code Remote SSH command"""
    if not command:
        return False
    
    vscode_patterns = [
        'bash', 'sh', '/bin/bash', '/bin/sh',  # VS Code starts shells
        'uname', 'whoami', 'id',                # VS Code system checks
        'test', '[', 'echo',                    # VS Code probing
        'mkdir', 'cd', 'pwd',                   # VS Code setup
        '.vscode-server',                       # VS Code server commands
        'wget', 'curl',                         # VS Code downloading
        'tar', 'unzip',                         # VS Code extracting
    ]
    
    # Check if command starts with any VS Code pattern
    for pattern in vscode_patterns:
        if command.startswith(pattern) or pattern in command:
            return True
    
    return False

def proxy_to_windows():
    """Proxy SSH connection to Windows host"""
    
    # Load environment variables from file
    load_environment()
    
    # Get Windows host details from environment
    windows_host = os.environ.get('WINDOWS_SSH_HOST', 'host.docker.internal')
    windows_port = os.environ.get('WINDOWS_SSH_PORT', '2221')
    
    # Get admin username (same as SSH router username)
    admin_username = os.environ.get('ADMIN_USERNAME')
    if not admin_username:
        print("Error: ADMIN_USERNAME environment variable required", file=sys.stderr)
        sys.exit(1)
    
    # Get the original SSH command if any
    original_command = os.environ.get('SSH_ORIGINAL_COMMAND', '')
    
    # Log connection for debugging (to stderr so it doesn't interfere)
    print(f"[SSH Router] Routing to Windows: {admin_username}@{windows_host}:{windows_port}", file=sys.stderr)
    if original_command:
        print(f"[SSH Router] Command: {original_command}", file=sys.stderr)
    
    # Build SSH command to proxy to Windows
    ssh_cmd = [
        'ssh',
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'LogLevel=ERROR',  # Reduce noise for VS Code
        '-p', windows_port,
        f"{admin_username}@{windows_host}"
    ]
    
    # Pass through the original command if present
    if original_command:
        # For VS Code commands, pass them through directly
        if is_vscode_command(original_command):
            ssh_cmd.append(original_command)
        else:
            # For other commands, pass through as-is
            ssh_cmd.append(original_command)
    
    try:
        # Execute the proxy connection
        os.execvp('ssh', ssh_cmd)
    except Exception as e:
        print(f"Error proxying to Windows: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    proxy_to_windows()