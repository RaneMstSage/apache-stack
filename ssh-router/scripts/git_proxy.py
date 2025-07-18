#!/usr/bin/env python3
"""
Git SSH Proxy - Routes Git SSH commands with LDAP authorization and database SSH key lookup
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
import hashlib

# Add MySQL import
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("Warning: mysql.connector not available, falling back to file-based auth")

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

def get_ssh_key_fingerprint():
    """Get the SSH key fingerprint from the current connection"""
    # Method 1: Try SSH_USER_AUTH file
    auth_file = os.environ.get('SSH_USER_AUTH', '')
    if auth_file and os.path.exists(auth_file):
        try:
            with open(auth_file, 'r') as f:
                content = f.read()
                logger.info(f"SSH_USER_AUTH file content: {content}")
                for line in content.splitlines():
                    if line.startswith('publickey '):
                        parts = line.strip().split()
                        if len(parts) >= 3:
                            # We have: publickey ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIK6Cir0yAdikmQ3hqSWAItkpX9hwIBO2KaV4edRmisTo
                            key_type = parts[1]
                            key_data = parts[2]
                            
                            # Convert to SHA256 fingerprint format that SSH uses
                            import base64
                            try:
                                key_bytes = base64.b64decode(key_data)
                                fingerprint_hash = hashlib.sha256(key_bytes).digest()
                                fingerprint = base64.b64encode(fingerprint_hash).decode('ascii').rstrip('=')
                                fingerprint = f"SHA256:{fingerprint}"
                                
                                logger.info(f"Converted key to fingerprint: {fingerprint}")
                                return fingerprint
                            except Exception as e:
                                logger.error(f"Error converting key to fingerprint: {e}")
                                return None
                            
        except Exception as e:
            logger.error(f"Error reading auth file: {e}")
    else:
        logger.warning(f"SSH_USER_AUTH not set or file does not exist: {auth_file}")

    # Method 2: Try environment variable
    fingerprint = os.environ.get('SSH_KEY_FINGERPRINT', '')
    if fingerprint:
        return fingerprint
    
    logger.warning("Could not extract SSH key fingerprint")
    return None

def get_user_from_database(fingerprint=None):
    """Query Redmine database for SSH key owner"""
    if not MYSQL_AVAILABLE:
        logger.warning("MySQL connector not available")
        return None
        
    try:
        # Connect to MySQL
        conn = mysql.connector.connect(
            host=os.environ.get('MYSQL_HOST', 'mysql'),
            database=os.environ.get('MYSQL_DATABASE', 'redmine'),
            user=os.environ.get('MYSQL_USER', 'redmine'),
            password=os.environ.get('MYSQL_PASSWORD'),
            port=int(os.environ.get('MYSQL_PORT', '3306'))
        )
        
        cursor = conn.cursor()
        
        if fingerprint:
            # Query by fingerprint (most reliable)
            # FIXED: Changed from sagemine_ssh_keys to sage_ssh_keys
            query = """
            SELECT u.login 
            FROM users u 
            JOIN sage_ssh_keys sk ON u.id = sk.user_id 
            WHERE sk.fingerprint = %s AND u.status = 1 AND sk.active = 1
            """
            cursor.execute(query, (fingerprint,))
        else:
            logger.warning("No fingerprint provided for database lookup")
            return None
            
        result = cursor.fetchone()
        
        if result:
            username = result[0]
            logger.info(f"Found user '{username}' for fingerprint '{fingerprint}' in database")
            return username
        else:
            logger.warning(f"No user found for fingerprint '{fingerprint}' in database")
            return None
            
    except Exception as e:
        logger.error(f"Database error: {e}")
        return None
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
    
    return None

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
    """Get the Redmine username associated with the SSH key used for authentication"""
    fingerprint = get_ssh_key_fingerprint()
    if fingerprint:
        logger.info(f"Using fingerprint: '{fingerprint}' for database lookup")
        db_user = get_user_from_database(fingerprint)
        if db_user:
            logger.info(f"User '{db_user}' found in Redmine database for fingerprint '{fingerprint}'")
            return db_user
        else:
            logger.warning(f"No user found in Redmine database for fingerprint '{fingerprint}'")
    else:
        logger.warning("Could not get SSH key fingerprint for database lookup")
    
    # No fallback - return None to force proper authentication
    return None

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
        
        # Get user's groups - try memberOf first, then search groups for membership
        user_dn, user_attrs = user_result[0]
        user_groups = []
        
        # Method 1: Try memberOf attribute (if LDAP has memberOf overlay)
        if 'memberOf' in user_attrs:
            for group_dn in user_attrs['memberOf']:
                group_dn_str = group_dn.decode('utf-8')
                if group_dn_str.startswith('cn='):
                    group_name = group_dn_str.split(',')[0].split('=')[1]
                    user_groups.append(group_name)
            logger.info(f"Found groups via memberOf: {user_groups}")
        
        # Method 2: Search groups that have this user as member (fallback)
        if not user_groups:
            logger.info(f"No memberOf found, searching groups for user membership")
            user_full_dn = user_dn
            group_search_base = f"ou=Groups,{ldap_base_dn}"
            group_filter = f"(member={user_full_dn})"
            group_results = conn.search_s(group_search_base, ldap.SCOPE_SUBTREE, group_filter, ['cn'])
            
            for group_dn, group_attrs in group_results:
                if 'cn' in group_attrs:
                    group_name = group_attrs['cn'][0].decode('utf-8')
                    user_groups.append(group_name)
            logger.info(f"Found groups via member search: {user_groups}")
        
        logger.info(f"User '{username}' LDAP groups: {user_groups}")
        
        # Check Git access requirements based on repository
        required_groups = []
        
        # Repository-specific group mapping (matching Apache config)
        if repo_name in ['apache-stack', 'openwebui-pipelines', 'openwebui-stack']:
            required_groups = ['proj-infrastructure', 'admins']
        elif repo_name in ['sage-repo-viewer', 'sage_checkout_plugin', 'SageDark', 'sagemine_ssh_keys']:
            required_groups = ['proj-mstsage-tools', 'admins']
        elif repo_name == 'Archmage':
            required_groups = ['proj-fullsail', 'admins']
        elif repo_name in ['UnityRPG', 'complete-unity-3d-dev-csharp']:
            required_groups = ['proj-gamedev', 'admins']
        elif repo_name in ['SchuetzKenneth_VFX_Unity', 'first-repo']:
            # Personal repos - check specific user OR admin
            if username == 'rane_mstsage':
                logger.info(f"Personal repository access granted for user '{username}'")
                # Still need to check local file system access below
            else:
                required_groups = ['admins']  # Only admins can access others' personal repos
        else:
            # Default: basic git access OR admin
            required_groups = ['git-users', 'admins']
            if is_write:
                required_groups = ['git-developers', 'admins']

        # Check if user has required LDAP groups (skip for personal repo owner)
        if required_groups:  # Only check if we have groups to check
            has_ldap_access = any(group in user_groups for group in required_groups)
            if not has_ldap_access:
                logger.warning(f"User '{username}' missing required LDAP groups for '{repo_name}': {required_groups}")
                return False
        
        # Also check local file system group membership
        # NOTE: Check SSH system user (git/svn), not LDAP user, for local groups
        ssh_user = os.environ.get('USER', 'unknown')

        try:
            # Get SSH system user info (git, svn, admin) - these exist in container
            user_info = pwd.getpwnam(ssh_user)
            local_groups = [g.gr_name for g in grp.getgrall() if ssh_user in g.gr_mem]
            
            # Add user's primary group
            primary_group = grp.getgrgid(user_info.pw_gid)
            local_groups.append(primary_group.gr_name)
            
            # Check if SSH system user is in apache-stack group (for file system permissions)
            if 'apache-stack' not in local_groups:
                logger.warning(f"SSH user '{ssh_user}' not in apache-stack group. Local groups: {local_groups}")
                return False
            
            logger.info(f"LDAP user '{username}' authorized, SSH user '{ssh_user}' has file system access")
            
        except (KeyError, OSError) as e:
            logger.error(f"Error checking local groups for SSH user '{ssh_user}': {str(e)}")
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