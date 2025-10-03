import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DVWA_HOST = os.getenv('DVWA_HOST')
DVWA_USER = os.getenv('DVWA_USER')
DVWA_PASSWORD = os.getenv('DVWA_PASSWORD')
DVWA_SSH_PORT = os.getenv('DVWA_SSH_PORT', '2222')
DVWA_SSH_KEY = os.getenv('DVWA_SSH_KEY')
DVWA_WEB_PATH = os.getenv('DVWA_WEB_PATH', '/var/www/html')
DVWA_DB_NAME = os.getenv('DVWA_DB_NAME', 'dvwa')
DVWA_DB_USER = os.getenv('DVWA_DB_USER', 'root')
DVWA_DB_PASSWORD = os.getenv('DVWA_DB_PASSWORD')
LOCAL_BACKUP_DIR = os.getenv('LOCAL_BACKUP_DIR')
GDRIVE_FOLDER_ID = os.getenv('GDRIVE_FOLDER_ID')

# Check required env vars
required_vars = [
    'DVWA_HOST', 'DVWA_USER', 'DVWA_DB_PASSWORD',
    'LOCAL_BACKUP_DIR', 'GDRIVE_FOLDER_ID'
]
for var in required_vars:
    if not os.getenv(var):
        print(f"Missing required env var: {var}")
        sys.exit(1)

# Ensure local backup directory exists
Path(LOCAL_BACKUP_DIR).mkdir(parents=True, exist_ok=True)

# Generate backup filename
date_str = datetime.now().strftime('%Y-%m-%d')
source_backup_file = f"dvwa_source_backup_{date_str}.tar.gz"
db_backup_file = f"dvwa_db_backup_{date_str}.sql"
local_source_backup = os.path.join(LOCAL_BACKUP_DIR, source_backup_file)
local_db_backup = os.path.join(LOCAL_BACKUP_DIR, db_backup_file)

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

print(f"Backing up DVWA from {DVWA_HOST}...")

# Step 1: Create source backup on remote server
print("Creating source code backup on remote server...")
remote_source_backup = f"/root/{source_backup_file}"
tar_cmd = f"cd {DVWA_WEB_PATH} && tar -czvf {remote_source_backup} dvwa/ && ls -lh {remote_source_backup}"

if ssh_auth[0] == 'sshpass':
    ssh_cmd = ssh_auth + [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT,
        f'{DVWA_USER}@{DVWA_HOST}',
        tar_cmd
    ]
else:
    ssh_cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT
    ] + ssh_auth + [
        f'{DVWA_USER}@{DVWA_HOST}',
        tar_cmd
    ]

result = subprocess.run(ssh_cmd)
if result.returncode != 0:
    print("Failed to create source backup on remote server.")
    sys.exit(1)

# Step 2: Create database backup on remote server
print("Creating database backup on remote server...")
remote_db_backup = f"/root/{db_backup_file}"
mysqldump_cmd = f"mysqldump -u {DVWA_DB_USER} -p'{DVWA_DB_PASSWORD}' {DVWA_DB_NAME} > {remote_db_backup} && ls -lh {remote_db_backup}"

if ssh_auth[0] == 'sshpass':
    ssh_cmd = ssh_auth + [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT,
        f'{DVWA_USER}@{DVWA_HOST}',
        mysqldump_cmd
    ]
else:
    ssh_cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT
    ] + ssh_auth + [
        f'{DVWA_USER}@{DVWA_HOST}',
        mysqldump_cmd
    ]

result = subprocess.run(ssh_cmd)
if result.returncode != 0:
    print("Failed to create database backup on remote server.")
    sys.exit(1)

# Step 3: Download source backup from remote server
print(f"Downloading source backup to {local_source_backup}...")
if ssh_auth[0] == 'sshpass':
    scp_cmd = ssh_auth + [
        'scp', '-o', 'StrictHostKeyChecking=no', '-P', DVWA_SSH_PORT,
        f'{DVWA_USER}@{DVWA_HOST}:{remote_source_backup}',
        local_source_backup
    ]
else:
    scp_cmd = [
        'scp', '-o', 'StrictHostKeyChecking=no', '-P', DVWA_SSH_PORT
    ] + ssh_auth + [
        f'{DVWA_USER}@{DVWA_HOST}:{remote_source_backup}',
        local_source_backup
    ]

result = subprocess.run(scp_cmd)
if result.returncode != 0:
    print("Failed to download source backup from remote server.")
    sys.exit(1)

print(f"Source backup downloaded to {local_source_backup}")

# Step 4: Download database backup from remote server
print(f"Downloading database backup to {local_db_backup}...")
if ssh_auth[0] == 'sshpass':
    scp_cmd = ssh_auth + [
        'scp', '-o', 'StrictHostKeyChecking=no', '-P', DVWA_SSH_PORT,
        f'{DVWA_USER}@{DVWA_HOST}:{remote_db_backup}',
        local_db_backup
    ]
else:
    scp_cmd = [
        'scp', '-o', 'StrictHostKeyChecking=no', '-P', DVWA_SSH_PORT
    ] + ssh_auth + [
        f'{DVWA_USER}@{DVWA_HOST}:{remote_db_backup}',
        local_db_backup
    ]

result = subprocess.run(scp_cmd)
if result.returncode != 0:
    print("Failed to download database backup from remote server.")
    sys.exit(1)

print(f"Database backup downloaded to {local_db_backup}")

# Step 5: Upload source backup to Google Drive
print(f"Uploading source backup to Google Drive folder {GDRIVE_FOLDER_ID}...")
gdrive_cmd = [
    'gdrive', 'files', 'upload', '--parent', GDRIVE_FOLDER_ID, local_source_backup
]
result = subprocess.run(gdrive_cmd)
if result.returncode != 0:
    print("Failed to upload source backup to Google Drive.")
    sys.exit(1)

print("Source backup uploaded to Google Drive successfully.")

# Step 6: Upload database backup to Google Drive
print(f"Uploading database backup to Google Drive folder {GDRIVE_FOLDER_ID}...")
gdrive_cmd = [
    'gdrive', 'files', 'upload', '--parent', GDRIVE_FOLDER_ID, local_db_backup
]
result = subprocess.run(gdrive_cmd)
if result.returncode == 0:
    print("Database backup uploaded to Google Drive successfully.")
    print("\nBackup completed successfully!")
else:
    print("Failed to upload database backup to Google Drive.")
    sys.exit(1)
