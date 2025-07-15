#!/usr/bin/env python3
"""
Git SSH Proxy - Routes Git SSH commands with LDAP authorization
"""
import os
import sys
import re
import subprocess
import shlex

def load_environment():
    """Load environment variables from file"""
    env_file = '/etc/ssh/ssh-router-env'
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('export '):
                    line = line[7:]
                if '=' in line:
                    key, value = line.split('=', 1)
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    os.environ[key] = value

def parse_git_command():
    """Parse the Git SSH command to extract repository and operation"""
    ssh_command = os.environ.get('SSH_ORIGINAL_COMMAND', '')
    
    if not ssh_command:
        print("Error: No Git command provided")
        sys.exit(1)
    
    # Git SSH commands look like:
    # git-upload-pack '/path/to/repo.git'  (for clone/fetch)
    # git-receive-pack '/path/to/repo.git' (for push)
    # git-upload-archive '/path/to/repo.git' (for archive)
    
    # Parse the command
    match = re.match(r"^(git-upload-pack|git-receive-pack|git-upload-archive)\s+'?/?([^']+)'?$", ssh_command)
    
    if not match:
        print(f"Error: Invalid Git command: {ssh_command}")
        sys.exit(1)
    
    command = match.group(1)
    repo_path = match.group(2)
    
    # Remove .git suffix if present for consistency
    if repo_path.endswith('.git'):
        repo_name = repo_path[:-4]
    else:
        repo_name = repo_path
    
    # Determine if this is a read or write operation
    is_write = (command == 'git-receive-pack')
    
    return command, repo_name, repo_path, is_write

def get_user_from_ssh_key():
    """Get the username associated with the SSH key used for authentication"""
    # SSH sets this when ForceCommand is used
    ssh_user = os.environ.get('USER', 'unknown')
    
    # For now, we'll need to implement a mapping from SSH keys to LDAP users
    # This could be done by:
    # 1. Storing username in authorized_keys comment field
    # 2. Maintaining a separate mapping file
    # 3. Using SSH certificates with embedded usernames
    
    # For Phase 2, we'll use a simple approach:
    # The authorized_keys file should have comments like:
    # ssh-rsa AAAA... user=rane_mstsage
    
    # TODO: Implement actual key-to-user mapping
    # For now, return a placeholder
    return "git_user"

def check_ldap_access(username, repo_name, is_write):
    """Check if user has access to repository via LDAP groups"""
    
    # For Phase 2 implementation, we'll add actual LDAP checking here
    # For now, just log what we would check
    
    print(f"Checking LDAP access for user '{username}' to repo '{repo_name}' (write={is_write})")
    
    # TODO: Implement actual LDAP group checking
    # This would:
    # 1. Connect to LDAP server
    # 2. Get user's groups
    # 3. Check against repository access rules
    # 4. Consider read vs write permissions
    
    # For now, return True to allow access
    return True

def execute_git_command(command, repo_name):
    """Execute the Git command on the actual repository"""
    
    # Get the Git repository base path
    git_repos_path = os.environ.get('GIT_REPOS_PATH', '/opt/repositories/git')
    
    # Build the full repository path
    repo_full_path = os.path.join(git_repos_path, f"{repo_name}.git")
    
    # Verify the repository exists
    if not os.path.exists(repo_full_path):
        print(f"Error: Repository not found: {repo_name}")
        sys.exit(1)
    
    # Build the command to execute
    git_cmd = [command, repo_full_path]
    
    print(f"Executing: {' '.join(git_cmd)}")
    
    try:
        # Execute the Git command
        # This replaces the current process with the Git command
        os.execvp(command, git_cmd)
    except Exception as e:
        print(f"Error executing Git command: {e}")
        sys.exit(1)

def main():
    """Main entry point for Git SSH routing"""
    
    # Load environment variables
    load_environment()
    
    # Parse the Git command
    try:
        command, repo_name, repo_path, is_write = parse_git_command()
    except Exception as e:
        print(f"Error parsing command: {e}")
        sys.exit(1)
    
    # Get the user from SSH key
    username = get_user_from_ssh_key()
    
    # Check LDAP access
    if not check_ldap_access(username, repo_name, is_write):
        print(f"Access denied: User '{username}' does not have {'write' if is_write else 'read'} access to '{repo_name}'")
        sys.exit(1)
    
    # Execute the Git command
    execute_git_command(command, repo_name)

if __name__ == "__main__":
    main()