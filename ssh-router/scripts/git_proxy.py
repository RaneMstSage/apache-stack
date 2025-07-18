#!/usr/bin/env python3
"""
Git SSH Proxy - Routes Git SSH commands with LDAP authorization
"""
import os
import sys
import re
import subprocess
import shlex
import logging
import ldap
import grp
import pwd

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
    """Get the LDAP username associated with the SSH key used for authentication"""
    import hashlib
    
    ssh_user = os.environ.get('USER', 'unknown')
    logger.info(f"SSH system user: {ssh_user}")
    
    # Method 1: Extract from authorized_keys comment
    if ssh_user in ['git', 'svn', 'admin']:
        keys_file = f"/etc/ssh/keys/{ssh_user}_authorized_keys"
        
        if os.path.exists(keys_file):
            try:
                # Get the public key from SSH connection
                ssh_key_type = os.environ.get('SSH_KEY_TYPE', '')
                ssh_key_data = os.environ.get('SSH_KEY_DATA', '')
                
                logger.info(f"Looking for key mapping in {keys_file}")
                
                with open(keys_file, 'r') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                            
                        # Parse: ssh-rsa AAAA...key... ldap_user=rane_mstsage
                        parts = line.split()
                        if len(parts) >= 2:
                            # Look for ldap_user= in any part
                            for part in parts:
                                if part.startswith('ldap_user='):
                                    ldap_username = part.split('=', 1)[1]
                                    logger.info(f"Found LDAP user mapping: {ssh_user} -> {ldap_username}")
                                    return ldap_username
                                    
            except Exception as e:
                logger.error(f"Error reading keys file {keys_file}: {e}")
    
    # Method 2: Use environment variable if set by SSH
    ldap_user = os.environ.get('LDAP_USER')
    if ldap_user:
        logger.info(f"Using LDAP_USER environment variable: {ldap_user}")
        return ldap_user
    
    # Method 3: Extract from SSH connection info
    ssh_connection = os.environ.get('SSH_CONNECTION', '')
    if ssh_connection:
        logger.info(f"SSH connection: {ssh_connection}")
        # You could implement IP-based mapping here
    
    # Fallback: Use SSH system user (not ideal for LDAP)
    logger.warning(f"No LDAP user mapping found, using SSH user: {ssh_user}")
    return ssh_user

def check_ldap_access(username, repo_name, is_write):
    """Check if user has access to repository via LDAP groups AND local groups"""
    
    try:
        # Load LDAP configuration
        ldap_host = os.environ.get('LDAP_HOST', 'openldap')
        ldap_port = int(os.environ.get('LDAP_PORT', '389'))
        ldap_base_dn = os.environ.get('LDAP_BASE_DN', 'dc=mstsage,dc=com')
        ldap_bind_dn = os.environ.get('LDAP_BIND_DN', 'cn=admin,dc=mstsage,dc=com')
        ldap_bind_password = os.environ.get('LDAP_BIND_PASSWORD', '')
        
        logger.info(f"Checking LDAP access for user '{username}' to repo '{repo_name}' (write={is_write})")
        
        # Connect to LDAP server
        ldap_uri = f"ldap://{ldap_host}:{ldap_port}"
        conn = ldap.initialize(ldap_uri)
        conn.set_option(ldap.OPT_REFERRALS, 0)
        conn.protocol_version = ldap.VERSION3
        
        # Bind with admin credentials
        conn.simple_bind_s(ldap_bind_dn, ldap_bind_password)
        
        # Search for the user
        user_search_base = f"ou=Users,{ldap_base_dn}"
        user_filter = f"(uid={username})"
        user_result = conn.search_s(user_search_base, ldap.SCOPE_SUBTREE, user_filter, ['memberOf'])
        
        if not user_result:
            logger.warning(f"User '{username}' not found in LDAP")
            return False
        
        # Get user's groups
        user_dn, user_attrs = user_result[0]
        user_groups = []
        
        if 'memberOf' in user_attrs:
            for group_dn in user_attrs['memberOf']:
                group_dn_str = group_dn.decode('utf-8')
                # Extract group name from DN (e.g., "cn=gitusers,ou=Groups,dc=mstsage,dc=com" -> "gitusers")
                if group_dn_str.startswith('cn='):
                    group_name = group_dn_str.split(',')[0].split('=')[1]
                    user_groups.append(group_name)
        
        logger.info(f"User '{username}' LDAP groups: {user_groups}")
        
        # Check Git access requirements
        required_groups = ['gitusers']  # Base requirement for Git access
        if is_write:
            required_groups.append('gitdevelopers')  # Additional requirement for write access
        
        # Check if user has required LDAP groups
        has_ldap_access = any(group in user_groups for group in required_groups)
        if not has_ldap_access:
            logger.warning(f"User '{username}' missing required LDAP groups: {required_groups}")
            return False
        
        # Also check local file system group membership
        try:
            # Get user info
            user_info = pwd.getpwnam(username)
            local_groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
            
            # Add user's primary group
            primary_group = grp.getgrgid(user_info.pw_gid)
            local_groups.append(primary_group.gr_name)
            
            # Check if user is in apache-stack group (for file system permissions)
            if 'apache-stack' not in local_groups:
                logger.warning(f"User '{username}' not in apache-stack group. Local groups: {local_groups}")
                return False
            
            logger.info(f"User '{username}' has both LDAP and local group access")
            
        except (KeyError, OSError) as e:
            logger.error(f"Error checking local groups for '{username}': {str(e})")
            return False
        
        conn.unbind_s()
        return True
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error for user '{username}': {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error checking access for '{username}': {str(e)}")
        return False

def execute_git_command(command, repo_name):
    """Execute the Git command on the actual repository"""
    
    # Get the Git repository base path
    git_repos_path = os.environ.get('GIT_REPOS_PATH', '/opt/repositories/git')
    
    # Build the full repository path
    repo_full_path = os.path.join(git_repos_path, f"{repo_name}.git")
    
    # Repository must exist - do not auto-create
    if not os.path.exists(repo_full_path):
        logger.error(f"Repository not found: {repo_name}")
        print(f"Error: Repository '{repo_name}' does not exist.")
        print("Repositories must be created by administrators.")
        sys.exit(1)
    
    # Verify it's a valid Git repository
    if not os.path.exists(os.path.join(repo_full_path, 'config')):
        logger.error(f"Invalid Git repository: {repo_name}")
        print(f"Error: '{repo_name}' is not a valid Git repository.")
        sys.exit(1)
    
    # Build the command to execute
    git_cmd = [command, repo_full_path]
    
    logger.info(f"Executing: {' '.join(git_cmd)}")
    
    try:
        # Execute the Git command
        os.execvp(command, git_cmd)
    except Exception as e:
        logger.error(f"Error executing Git command: {e}")
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