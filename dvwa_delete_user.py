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

# Check if username is provided
if len(sys.argv) < 2:
    print("Usage: python3 dvwa_delete_user.py <username>")
    print("\nExample: python3 dvwa_delete_user.py john123")
    sys.exit(1)

username_to_delete = sys.argv[1]

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
print(f"Searching for user '{username_to_delete}' in database '{DVWA_DB_NAME}'...\n")

# Step 1: Check if user exists and show user info
check_user_cmd = f"mysql -u {DVWA_DB_USER} -p'{DVWA_DB_PASSWORD}' {DVWA_DB_NAME} -e \"SELECT user_id AS 'ID', first_name AS 'First Name', last_name AS 'Last Name', user AS 'Username', avatar AS 'Avatar', last_login AS 'Last Login', failed_login AS 'Failed Logins' FROM users WHERE user = '{username_to_delete}';\""

if ssh_auth[0] == 'sshpass':
    ssh_cmd = ssh_auth + [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT,
        f'{DVWA_USER}@{DVWA_HOST}',
        check_user_cmd
    ]
else:
    ssh_cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT
    ] + ssh_auth + [
        f'{DVWA_USER}@{DVWA_HOST}',
        check_user_cmd
    ]

result = subprocess.run(ssh_cmd, capture_output=True, text=True)

if result.returncode != 0:
    print("Failed to query database.")
    sys.exit(1)

# Check if user exists
if not result.stdout.strip() or 'ID' in result.stdout and len(result.stdout.strip().split('\n')) < 2:
    print(f"❌ User '{username_to_delete}' not found in database.")
    sys.exit(1)

# Display user info
print("User found:")
print(result.stdout)

# Step 2: Ask for confirmation
print(f"\n⚠️  Are you sure you want to delete user '{username_to_delete}'?")
confirmation = input("Type 'yes' to confirm: ")

if confirmation.lower() != 'yes':
    print("Deletion cancelled.")
    sys.exit(0)

# Step 3: Delete the user
print(f"\nDeleting user '{username_to_delete}'...")
delete_cmd = f"mysql -u {DVWA_DB_USER} -p'{DVWA_DB_PASSWORD}' {DVWA_DB_NAME} -e \"DELETE FROM users WHERE user = '{username_to_delete}';\""

if ssh_auth[0] == 'sshpass':
    ssh_cmd = ssh_auth + [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT,
        f'{DVWA_USER}@{DVWA_HOST}',
        delete_cmd
    ]
else:
    ssh_cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT
    ] + ssh_auth + [
        f'{DVWA_USER}@{DVWA_HOST}',
        delete_cmd
    ]

result = subprocess.run(ssh_cmd)

if result.returncode != 0:
    print("\nFailed to delete user from database.")
    sys.exit(1)

# Step 4: Verify deletion
print("Verifying deletion...")
verify_cmd = f"mysql -u {DVWA_DB_USER} -p'{DVWA_DB_PASSWORD}' {DVWA_DB_NAME} -sN -e \"SELECT COUNT(*) FROM users WHERE user = '{username_to_delete}';\""

if ssh_auth[0] == 'sshpass':
    ssh_cmd = ssh_auth + [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT,
        f'{DVWA_USER}@{DVWA_HOST}',
        verify_cmd
    ]
else:
    ssh_cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT
    ] + ssh_auth + [
        f'{DVWA_USER}@{DVWA_HOST}',
        verify_cmd
    ]

result = subprocess.run(ssh_cmd, capture_output=True, text=True)

if result.returncode == 0:
    count = result.stdout.strip()
    if count == '0':
        print(f"\n✅ User '{username_to_delete}' deleted successfully!")
    else:
        print(f"\n⚠️  Warning: User may still exist in database.")
else:
    print("\nFailed to verify deletion.")
    sys.exit(1)
