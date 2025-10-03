import os
import subprocess
import sys
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DVWA_HOST = os.getenv('DVWA_HOST')
DVWA_USER = os.getenv('DVWA_USER')
DVWA_PASSWORD = os.getenv('DVWA_PASSWORD')
DVWA_SSH_PORT = os.getenv('DVWA_SSH_PORT', '2222')
DVWA_SSH_KEY = os.getenv('DVWA_SSH_KEY')
DVWA_DB_NAME = os.getenv('DVWA_DB_NAME', 'dvwa')
DVWA_DB_USER = os.getenv('DVWA_DB_USER', 'root')
DVWA_DB_PASSWORD = os.getenv('DVWA_DB_PASSWORD')

# Check required env vars
required_vars = [
    'DVWA_HOST', 'DVWA_USER', 'DVWA_DB_PASSWORD'
]
for var in required_vars:
    if not os.getenv(var):
        print(f"Missing required env var: {var}")
        sys.exit(1)

# Determine SSH authentication method
ssh_auth = []
if DVWA_SSH_KEY and os.path.exists(os.path.expanduser(DVWA_SSH_KEY)):
    ssh_auth = ['-i', os.path.expanduser(DVWA_SSH_KEY)]
elif DVWA_PASSWORD:
    # Check for sshpass
    if subprocess.call(['which', 'sshpass'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
        print("sshpass is required for password authentication. Please install it (e.g., brew install hudochenkov/sshpass/sshpass).")
        sys.exit(1)
    ssh_auth = ['sshpass', '-p', DVWA_PASSWORD]
else:
    print("Either DVWA_SSH_KEY or DVWA_PASSWORD must be provided.")
    sys.exit(1)

print(f"Connecting to {DVWA_HOST} via SSH...")
print(f"Querying users from database '{DVWA_DB_NAME}'...\n")

# MySQL query to get all users
mysql_cmd = f"mysql -u {DVWA_DB_USER} -p'{DVWA_DB_PASSWORD}' {DVWA_DB_NAME} -e \"SELECT user_id AS 'ID', first_name AS 'First Name', last_name AS 'Last Name', user AS 'Username', avatar AS 'Avatar', last_login AS 'Last Login', failed_login AS 'Failed Logins' FROM users ORDER BY user_id;\""

# Build SSH command
if ssh_auth[0] == 'sshpass':
    ssh_cmd = ssh_auth + [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT,
        f'{DVWA_USER}@{DVWA_HOST}',
        mysql_cmd
    ]
else:
    ssh_cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT
    ] + ssh_auth + [
        f'{DVWA_USER}@{DVWA_HOST}',
        mysql_cmd
    ]

# Execute SSH command
result = subprocess.run(ssh_cmd)

if result.returncode != 0:
    print("\nFailed to query users from database.")
    sys.exit(1)

print("\nQuery completed successfully!")
