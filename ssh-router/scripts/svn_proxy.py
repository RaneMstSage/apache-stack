#!/usr/bin/env python3
"""
SVN SSH Proxy Handler
Routes SVN commands via SSH to SVN Repository
"""

import os
import sys
import re
import subprocess
import logging
import ldap

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/var/log/svn_proxy.log',
)
logger = logging.getLogger('svn_proxy')

# SVN Repository base path
SVN_REPOS_PATH = "/opt/repositories/svn"

def load_environment():
    """
    Load environment variables from the shared file created by entrypoint.sh

    Returns:
        dict: Environment variables loaded from the file
    """
    env = {}
    env_file = '/etc/ssh/ssh-router-env'

    if os.path.exists(env_file):
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('export '):
                        line = line.replace('export ', '', 1)
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        # Remove quotes if present
                        value = value.strip('"\'')
                        env[key] = value
        except Exception as e:
            logging.error(f"Error loading environment: {str(e)}")

    return env

def get_environment_var(name, default=None):
    """
    Get an environment variable, first checking the environment , then the shared file

    Args:
        name (str): Name of the the environment variable
        default: Default value if not found

    Returns:
        str: Value of the environment variable or default
    """
    # First check actual environment
    if name in os.environ:
        return os.environ[name]

    # Then check loaded environment
    env = load_environment()
    return env.get(name, default)

def parse_svn_command():
    """
    Parse the SVN SSH command from SSH_ORIGINAL_COMMAND environment variable

    SVN uses svnserve with -t option for tunnel mode when accessing via SSH.
    Format: svnserve -t [--tunnel-user=username]
    """
    original_command = os.environ.get('SSH_ORIGINAL_COMMAND', '')
    logger.info(f"Original command: {original_command}")

    # Basic validation - must start with svnserve
    if not original_command.startswith('svnserve '):
        logger.error(f"Invalid SVN command: {original_command}")
        sys.stderr.write("Error: Not a valid SVN command\n")
        sys.exit(1)

    # Ensure tunnel mode is requested
    if '-t' not in original_command and '--tunnel' not in original_command:
        logger.error(f"SVN command not in tunnel mode: {original_command}")
        sys.stderr.write("Error: SVN must use tunnel mode via SSH\n")
        sys.exit(1)
    
    # Parse Repository path if specified
    repo_path = None
    match = re.search(r'--root=([^\s]+)', original_command)
    if match:
        repo_path = match.group(1)

    return {
        'command': original_command,
        'repo_path': repo_path,
    }

def check_ldap_access(username, repo_path=None, is_write=False):
    """
    Check if the user has access to SVN repositories via LDAP groups AND local groups

    Args:
        username (str): Username to check
        repo_path (str, optional): Repository path
        is_write (bool): whether write access is needed

    Returns:
        bool: True if access granted, false otherwise
    """
    try:
        # First check LDAP authentication (existing code)
        env = load_environment()
        
        # Extract LDAP settings from environment
        ldap_server = f"ldap://{env.get('LDAP_HOST', 'openldap')}:{env.get('LDAP_PORT', '389')}"
        ldap_base_dn = env.get('LDAP_BASE_DN', 'dc=mstsage,dc=com')
        ldap_bind_dn = env.get('LDAP_BIND_DN', f"cn=admin,{ldap_base_dn}")
        ldap_bind_password = env.get('LDAP_BIND_PASSWORD', '')
        
        logger.info(f"Connecting to LDAP server: {ldap_server}")
        
        # Connect to LDAP
        conn = ldap.initialize(ldap_server)
        conn.simple_bind_s(ldap_bind_dn, ldap_bind_password)
        
        # Search for the user
        user_filter = f"(&(objectClass=inetOrgPerson)(uid={username}))"
        user_attrs = ['memberOf']
        
        logger.info(f"Searching for user: {username}")
        result = conn.search_s(ldap_base_dn, ldap.SCOPE_SUBTREE, user_filter, user_attrs)
        
        if not result:
            logger.warning(f"User {username} not found in LDAP")
            return False
        
        # Check group membership
        user_dn, user_attrs = result[0]
        
        if 'memberOf' not in user_attrs:
            logger.warning(f"User {username} has no group memberships")
            return False
        
        groups = user_attrs['memberOf']
        if isinstance(groups, bytes):
            groups = [groups]
            
        # Convert bytes to strings if needed
        groups = [g.decode('utf-8') if isinstance(g, bytes) else g for g in groups]
        
        # Check for required group memberships
        svn_users_group = f"cn=svnusers,ou=Groups,{ldap_base_dn}"
        svn_developers_group = f"cn=svndevelopers,ou=Groups,{ldap_base_dn}"
        
        # If repository-specific access is needed, we can check for specialized groups
        if repo_path:
            repo_name = os.path.basename(repo_path)
            repo_specific_read = f"cn=svn-{repo_name}-users,ou=Groups,{ldap_base_dn}"
            repo_specific_write = f"cn=svn-{repo_name}-developers,ou=Groups,{ldap_base_dn}"
            
            # Check if user is in repo-specific groups
            has_read_access = svn_users_group in groups or repo_specific_read in groups
            has_write_access = svn_developers_group in groups or repo_specific_write in groups
        else:
            # Just check the general SVN groups
            has_read_access = svn_users_group in groups
            has_write_access = svn_developers_group in groups
        
        if is_write and not has_write_access:
            logger.warning(f"User {username} does not have SVN write access")
            return False
            
        if not has_read_access and not has_write_access:
            logger.warning(f"User {username} does not have SVN access")
            return False
            
        logger.info(f"User {username} has SVN access (write={is_write})")
        
        # After LDAP validation succeeds, check local group membership
        import grp
        import pwd
        
        try:
            # Get user info
            user_info = pwd.getpwnam(username)
            user_groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
            
            # Add user's primary group
            primary_group = grp.getgrgid(user_info.pw_gid)
            user_groups.append(primary_group.gr_name)
            
            # Check if user is in apache-stack group (for file system permissions)
            if 'apache-stack' not in user_groups:
                logger.warning(f"User {username} not in apache-stack group. Groups: {user_groups}")
                return False

            logger.info(f"User {username} has both LDAP and apache-stack group access")
            
        except (KeyError, OSError) as e:
            logger.error(f"Error checking local groups for {username}: {str(e)}")
            return False
        
        return True
        
    except ldap.LDAPError as e:
        logger.error(f"LDAP error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Error checking access: {str(e)}")
        return False

def get_user_from_ssh_key():
    """Get the LDAP username associated with the SSH key used for authentication"""
    # Same implementation as git_proxy.py
    ssh_user = os.environ.get('USER', 'unknown')
    logger.info(f"SSH system user: {ssh_user}")
    
    if ssh_user in ['git', 'svn', 'admin']:
        keys_file = f"/etc/ssh/keys/{ssh_user}_authorized_keys"
        
        if os.path.exists(keys_file):
            try:
                with open(keys_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                            
                        parts = line.split()
                        for part in parts:
                            if part.startswith('user='):
                                ldap_username = part.split('=', 1)[1]
                                logger.info(f"Found LDAP user mapping: {ssh_user} -> {ldap_username}")
                                return ldap_username
                                
            except Exception as e:
                logger.error(f"Error reading keys file {keys_file}: {e}")
    
    logger.warning(f"No LDAP user mapping found, using SSH user: {ssh_user}")
    return ssh_user

# Update execute_svn_command to use proper user resolution:
def execute_svn_command(command_info):
    """Execute the SVN command (svnserve)"""
    try:
        username = get_user_from_ssh_key()  # ✅ Use proper mapping
        command = command_info['command']
        repo_path = command_info['repo_path']

        # Get SVN repos path from environment
        svn_repos_path = get_environment_var('SVN_REPOS_PATH', SVN_REPOS_PATH)
        
        # Verify SVN repositories directory exists
        if not os.path.exists(svn_repos_path):
            logger.error(f"SVN repositories directory not found: {svn_repos_path}")
            sys.stderr.write("Error: SVN repositories not available.\n")
            sys.exit(1)

        # Validate access (but don't auto-create)
        if not check_ldap_access(username, repo_path):
            sys.stderr.write(f"Access denied for user {username}\n")
            sys.exit(1)
        
        # Execute svnserve command - let it handle repository validation
        logger.info(f"Executing SVN command for user {username}: {command}")

        # Use explicit svnserve path
        svnserve_path = "/usr/local/bin/svnserve"  # Your custom build
        command = command.replace("svnserve ", f"{svnserve_path} ")

        # Add --root option to point to repositories
        if "--root=" not in command:
            command = f"{command} --root={svn_repos_path}"

        logger.info(f"Running command: {command}")

        # Execute and pass through stdin/stdout/stderr
        process = subprocess.Popen(
            command,
            shell=True,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

        process.wait()
        return process.returncode

    except Exception as e:
        logger.error(f"Error executing SVN command: {str(e)}")
        sys.stderr.write(f"Error: {str(e)}\n")
        return 1

def main():
    """Main SVN Proxy handler"""
    try:
        # Parse SVN command
        command_info = parse_svn_command()

        # Execute the SVN command
        exit_code = execute_svn_command(command_info)

        # Exit with the same code
        sys.exit(exit_code)

    except Exception as e:
        logger.error(f"Unhandled exception: {str(e)}")
        sys.stderr.write(f"Error: {str(e)}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()