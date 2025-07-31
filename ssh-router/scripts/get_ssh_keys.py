#!/usr/bin/env python3
"""
SSH Authorized Keys Lookup Script
Retrieves SSH public keys from Redmine database for SSH authentication
"""
import sys
import os
import logging
import mysql.connector

# Set up logging to stderr (SSH reads stdout for keys)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
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

def get_keys_from_database(username):
    """Query Redmine database for user's SSH keys"""
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

        # For git and svn users, get ALL active keys from ALL users
        if username in ['git', 'svn']:
            query = """
            SELECT sk.key
            FROM sage_ssh_keys sk
            JOIN users u ON u.id = sk.user_id
            WHERE u.status = 1 AND sk.active = 1
            """
            cursor.execute(query)
            logger.info(f"Fetching all active SSH keys for {username} service")
        else:
            # For other users (like admin), return nothing - use static files
            logger.info(f"User {username} should use static authorized_keys file")
            return

        results = cursor.fetchall()

        # Output each key on a separate line to stdout
        key_count = 0
        for row in results:
            key = row[0].strip()
            if key:
                print(key)
                key_count += 1

        logger.info(f"Retrieved {key_count} SSH keys for {username}")

    except Exception as e:
        logger.error(f"Database error: {e}")

    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        logger.error("Usage: get_ssh_keys.py <username>")
        sys.exit(1)

    username = sys.argv[1]
    logger.info(f"Looking up SSH keys for user: {username}")

    # Load environment variables
    load_environment()

    # Get and output keys
    get_keys_from_database(username)

if __name__ == "__main__":
    main()