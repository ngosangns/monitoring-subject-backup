import os
import subprocess
import sys
import random
import hashlib
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

# Generate random user data
first_names = ['John', 'Jane', 'Mike', 'Sarah', 'David', 'Emma', 'Chris', 'Lisa', 'Tom', 'Anna']
last_names = ['Smith', 'Johnson', 'Brown', 'Taylor', 'Wilson', 'Davis', 'Miller', 'Moore', 'Anderson', 'Thomas']

random_first = random.choice(first_names)
random_last = random.choice(last_names)
random_username = f"{random_first.lower()}{random.randint(100, 999)}"
random_password = f"Pass{random.randint(1000, 9999)}"
random_avatar = f"/hackable/users/{random_username}.jpg"

# Generate MD5 hash of password (DVWA uses MD5)
password_hash = hashlib.md5(random_password.encode()).hexdigest()

print(f"Connecting to {DVWA_HOST} via SSH...")
print(f"Adding new user to database '{DVWA_DB_NAME}'...\n")

# Step 1: Get the next available user_id
print("Getting next available user ID...")
get_max_id_cmd = f"mysql -u {DVWA_DB_USER} -p'{DVWA_DB_PASSWORD}' {DVWA_DB_NAME} -sN -e \"SELECT COALESCE(MAX(user_id), 0) + 1 FROM users;\""

if ssh_auth[0] == 'sshpass':
    ssh_cmd = ssh_auth + [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT,
        f'{DVWA_USER}@{DVWA_HOST}',
        get_max_id_cmd
    ]
else:
    ssh_cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT
    ] + ssh_auth + [
        f'{DVWA_USER}@{DVWA_HOST}',
        get_max_id_cmd
    ]

result = subprocess.run(ssh_cmd, capture_output=True, text=True)
if result.returncode != 0:
    print("Failed to get next user ID from database.")
    sys.exit(1)

next_user_id = result.stdout.strip()
print(f"Next user ID: {next_user_id}")

# Step 2: Insert new user
print(f"\nInserting new user...")
print(f"  Username: {random_username}")
print(f"  Password: {random_password}")
print(f"  Name: {random_first} {random_last}")
print(f"  Avatar: {random_avatar}\n")

insert_cmd = f"mysql -u {DVWA_DB_USER} -p'{DVWA_DB_PASSWORD}' {DVWA_DB_NAME} -e \"INSERT INTO users (user_id, first_name, last_name, user, password, avatar, failed_login) VALUES ({next_user_id}, '{random_first}', '{random_last}', '{random_username}', '{password_hash}', '{random_avatar}', 0);\""

if ssh_auth[0] == 'sshpass':
    ssh_cmd = ssh_auth + [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT,
        f'{DVWA_USER}@{DVWA_HOST}',
        insert_cmd
    ]
else:
    ssh_cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT
    ] + ssh_auth + [
        f'{DVWA_USER}@{DVWA_HOST}',
        insert_cmd
    ]

result = subprocess.run(ssh_cmd)

if result.returncode != 0:
    print("\nFailed to insert user into database.")
    sys.exit(1)

# Step 3: Verify the user was added
print("Verifying user was added successfully...")
verify_cmd = f"mysql -u {DVWA_DB_USER} -p'{DVWA_DB_PASSWORD}' {DVWA_DB_NAME} -e \"SELECT user_id AS 'ID', first_name AS 'First Name', last_name AS 'Last Name', user AS 'Username', avatar AS 'Avatar', last_login AS 'Last Login', failed_login AS 'Failed Logins' FROM users WHERE user_id = {next_user_id};\""

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

result = subprocess.run(ssh_cmd)

if result.returncode == 0:
    print(f"\n✅ User added successfully!")
    print(f"\n📝 Login credentials:")
    print(f"   Username: {random_username}")
    print(f"   Password: {random_password}")
else:
    print("\nFailed to verify user addition.")
    sys.exit(1)
