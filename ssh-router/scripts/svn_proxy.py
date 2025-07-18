#!/usr/bin/env python3
"""
SVN SSH Proxy Handler
Routes SVN commands via SSH to SVN Repository with database SSH key lookup
"""

import os
import sys
import re
import subprocess
import logging
import ldap
import pwd
import grp

# Add MySQL import
try:
    import mysql.connector
    MYSQL_AVAILABLE = True
except ImportError:
    MYSQL_AVAILABLE = False
    print("Warning: mysql.connector not available, falling back to file-based auth")

# Set up logging to both file and console for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/svn_proxy.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('svn_proxy')

# SVN Repository base path
SVN_REPOS_PATH = "/opt/repositories/svn"

def load_environment():
    """
    Load environment variables from the shared file created by entrypoint.sh
    and apply them to os.environ (same as git_proxy.py)
    """
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
                        os.environ[key] = value
            logger.info(f"Loaded environment variables from {env_file}")
        except Exception as e:
            logger.error(f"Error loading environment: {str(e)}")
    else:
        logger.warning(f"Environment file not found: {env_file}")

def get_environment_var(name, default=None):
    """
    Get an environment variable from os.environ
    
    Args:
        name (str): Name of the environment variable
        default: Default value if not found

    Returns:
        str: Value of the environment variable or default
    """
    return os.environ.get(name, default)

def get_ssh_key_fingerprint():
    """Get the SSH key fingerprint from the current connection"""
    # SSH doesn't directly provide this, but we can try to get it from the environment
    # This requires sshd to be configured with: ExposeAuthInfo yes
    auth_file = os.environ.get('SSH_USER_AUTH', '')
    if auth_file and os.path.exists(auth_file):
        try:
            with open(auth_file, 'r') as f:
                for line in f:
                    if line.startswith('publickey '):
                        # Extract fingerprint from the line
                        parts = line.strip().split()
                        if len(parts) >= 2:
                            return parts[1]
        except Exception as e:
            logger.error(f"Error reading auth file: {e}")
    
    # Alternative: Try to get from environment if set by custom sshd
    return os.environ.get('SSH_KEY_FINGERPRINT', '')

def get_user_from_database(fingerprint=None):
    """Query Redmine database for SSH key owner"""
    if not MYSQL_AVAILABLE:
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
            query = """
            SELECT u.login 
            FROM sage_ssh_keys s
            JOIN users u ON s.user_id = u.id
            WHERE s.fingerprint = %s AND s.active = 1
            LIMIT 1
            """
            cursor.execute(query, (fingerprint,))
        else:
            # Fallback: This would need more complex matching
            # For now, return None
            return None
            
        result = cursor.fetchone()
        
        if result:
            logger.info(f"Found user from database: {result[0]}")
            return result[0]
            
    except Exception as e:
        logger.error(f"Database error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
    
    return None

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

def get_user_from_ssh_key():
    """Get the LDAP username associated with the SSH key used for authentication"""
    ssh_user = os.environ.get('USER', 'unknown')
    logger.info(f"SSH system user: {ssh_user}")
    
    # First, try database lookup if enabled
    if MYSQL_AVAILABLE and os.environ.get('USE_DATABASE_AUTH', 'false').lower() == 'true':
        fingerprint = get_ssh_key_fingerprint()
        if fingerprint:
            db_user = get_user_from_database(fingerprint)
            if db_user:
                return db_user
        else:
            logger.warning("Could not get SSH key fingerprint for database lookup")
    
    # Fallback to file-based authentication
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

def check_ldap_access(username, repo_path=None, is_write=False):
    """Check if user has access to SVN repository via LDAP groups AND local groups"""
    
    try:
        # Load LDAP configuration (same as git_proxy.py)
        ldap_host = os.environ.get('LDAP_HOST', 'openldap')
        ldap_port = int(os.environ.get('LDAP_PORT', '389'))
        ldap_base_dn = os.environ.get('LDAP_BASE_DN', 'dc=mstsage,dc=com')
        ldap_bind_dn = os.environ.get('LDAP_BIND_DN', 'cn=admin,dc=mstsage,dc=com')
        ldap_bind_password = os.environ.get('LDAP_BIND_PASSWORD', '')
        
        logger.info(f"Checking LDAP access for user '{username}' to SVN repo '{repo_path}' (write={is_write})")
        
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
        
        # Get user's groups using member search (same as git_proxy.py)
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
        
        # SVN Repository-specific group mapping (matching Apache config)
        required_groups = []
        repo_name = None
        
        if repo_path:
            # Extract repository collection from path
            path_parts = repo_path.strip('/').split('/')
            if len(path_parts) > 0:
                repo_name = path_parts[0]  # First part is the collection name
        
        # Map SVN collections to LDAP groups (based on your Apache config)
        if repo_name in ['alt_night']:
            # Personal repos - check specific user OR admin
            if username == 'alt_night':
                logger.info(f"Personal repository access granted for user '{username}'")
            else:
                required_groups = ['admins']
        elif repo_name in ['kschuetz']:
            # Personal repos - check specific user OR admin  
            if username == 'rane_mstsage':
                logger.info(f"Personal repository access granted for user '{username}'")
            else:
                required_groups = ['admins']
        elif repo_name in ['wagganjr']:
            # Personal repos - check specific user OR admin
            if username == 'wagganjr':
                logger.info(f"Personal repository access granted for user '{username}'")
            else:
                required_groups = ['admins']
        elif repo_name in ['zupaxis']:
            # Personal repos - check specific user OR admin
            if username == 'ZupAxis':
                logger.info(f"Personal repository access granted for user '{username}'")
            else:
                required_groups = ['admins']
        elif repo_name in ['fullsail']:
            # Educational repositories
            required_groups = ['proj-fullsail', 'admins']
        elif repo_name in ['cgprojects', 'smashingpumpkins']:
            # PumpkinHead Studios projects
            required_groups = ['org-pumpkinhead', 'admins']
        elif repo_name in ['codingprojects', 'kineticheart']:
            # MstSage Entertainment projects
            required_groups = ['org-mstsage', 'admins']
        elif repo_name in ['gamedev']:
            # Game development projects
            required_groups = ['proj-cgprojects', 'admins']
        elif repo_name in ['tutorials']:
            # Tutorial repositories
            required_groups = ['proj-tutorials', 'admins']
        else:
            # Default: basic SVN access OR admin
            required_groups = ['svn-users', 'admins']
            if is_write:
                required_groups = ['svn-developers', 'admins']

        # Check if user has required LDAP groups (skip for personal repo owner)
        if required_groups:  # Only check if we have groups to check
            has_ldap_access = any(group in user_groups for group in required_groups)
            if not has_ldap_access:
                logger.warning(f"User '{username}' missing required LDAP groups for '{repo_name}': {required_groups}")
                return False
        
        # Also check local file system group membership
        # NOTE: Check SSH system user (svn), not LDAP user, for local groups
        ssh_user = os.environ.get('USER', 'unknown')

        try:
            # Get SSH system user info (svn, git, admin) - these exist in container
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

def execute_svn_command(command_info):
    """Execute the SVN command (svnserve)"""
    try:
        username = get_user_from_ssh_key()
        command = command_info['command']
        repo_path = command_info['repo_path']

        # Get SVN repos path from environment
        svn_repos_path = get_environment_var('SVN_REPOS_PATH', SVN_REPOS_PATH)
        
        # Verify SVN repositories directory exists
        if not os.path.exists(svn_repos_path):
            logger.error(f"SVN repositories directory not found: {svn_repos_path}")
            sys.stderr.write("Error: SVN repositories not available.\n")
            sys.exit(1)

        # Determine if this is a write operation (SVN doesn't have clear read/write distinction like Git)
        # For SVN+SSH, we'll assume write access is needed (more secure default)
        is_write = True  # SVN+SSH typically needs write access
        
        # Validate access with proper parameters (matching git_proxy.py pattern)
        if not check_ldap_access(username, repo_path, is_write):
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

def extract_repo_path_from_ssh():
    """Extract repository path from SSH command for SVN+SSH protocol"""
    # For svn+ssh://server/path, the path comes after the hostname
    # SVN will pass this as arguments to svnserve
    
    # Check for repository path in command arguments
    original_command = os.environ.get('SSH_ORIGINAL_COMMAND', '')
    logger.info(f"Extracting repo path from command: {original_command}")
    
    # SVN+SSH typically doesn't use --root, path is implicit
    # Let's also check sys.argv for any path information
    logger.info(f"Command arguments: {sys.argv}")
    
    # For now, try to extract from SSH connection info if available
    # This might be passed in environment or command line
    return None  # Will rely on Apache config for path-based access

def main():
    """Main SVN Proxy handler"""
    try:
        # Load environment variables
        load_environment()
        
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