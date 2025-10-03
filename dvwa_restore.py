import os
import subprocess
import sys
from dotenv import load_dotenv
from pathlib import Path

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
GDRIVE_SOURCE_FILE_ID = os.getenv('GDRIVE_SOURCE_FILE_ID')  # Google Drive file ID for source backup
GDRIVE_DB_FILE_ID = os.getenv('GDRIVE_DB_FILE_ID')  # Google Drive file ID for database backup

# Check required env vars
required_vars = [
    'DVWA_HOST', 'DVWA_USER', 'DVWA_DB_PASSWORD',
    'LOCAL_BACKUP_DIR', 'GDRIVE_SOURCE_FILE_ID', 'GDRIVE_DB_FILE_ID'
]
for var in required_vars:
    if not os.getenv(var):
        print(f"Missing required env var: {var}")
        sys.exit(1)

# Ensure local backup directory exists
Path(LOCAL_BACKUP_DIR).mkdir(parents=True, exist_ok=True)

# Helper function to find downloaded file
def get_downloaded_filename(folder, file_id):
    # gdrive names the file as <file_id> if the original name is not available
    for f in os.listdir(folder):
        if file_id in f:
            return os.path.join(folder, f)
    # fallback: return the most recent file
    files = [os.path.join(folder, f) for f in os.listdir(folder)]
    if files:
        return max(files, key=os.path.getctime)
    return None

# Step 1: Download source backup from Google Drive
print(f"Downloading source backup from Google Drive (ID: {GDRIVE_SOURCE_FILE_ID})...")
gdrive_download_cmd = [
    'gdrive', 'files', 'download', '--destination', LOCAL_BACKUP_DIR, '--overwrite', GDRIVE_SOURCE_FILE_ID
]
result = subprocess.run(gdrive_download_cmd)
if result.returncode != 0:
    print("Failed to download source backup from Google Drive.")
    sys.exit(1)

local_source_backup = get_downloaded_filename(LOCAL_BACKUP_DIR, GDRIVE_SOURCE_FILE_ID)
if not local_source_backup:
    print("Could not find downloaded source backup file.")
    sys.exit(1)
print(f"Source backup downloaded to {local_source_backup}")

# Step 2: Download database backup from Google Drive
print(f"Downloading database backup from Google Drive (ID: {GDRIVE_DB_FILE_ID})...")
gdrive_download_cmd = [
    'gdrive', 'files', 'download', '--destination', LOCAL_BACKUP_DIR, '--overwrite', GDRIVE_DB_FILE_ID
]
result = subprocess.run(gdrive_download_cmd)
if result.returncode != 0:
    print("Failed to download database backup from Google Drive.")
    sys.exit(1)

local_db_backup = get_downloaded_filename(LOCAL_BACKUP_DIR, GDRIVE_DB_FILE_ID)
if not local_db_backup:
    print("Could not find downloaded database backup file.")
    sys.exit(1)
print(f"Database backup downloaded to {local_db_backup}")

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

print(f"Restoring DVWA to {DVWA_HOST}...")

# Step 3: Upload source backup to remote server
remote_source_backup = f"/tmp/{os.path.basename(local_source_backup)}"
print(f"Uploading source backup to remote server...")

if ssh_auth[0] == 'sshpass':
    scp_cmd = ssh_auth + [
        'scp', '-o', 'StrictHostKeyChecking=no', '-P', DVWA_SSH_PORT,
        local_source_backup,
        f'{DVWA_USER}@{DVWA_HOST}:{remote_source_backup}'
    ]
else:
    scp_cmd = [
        'scp', '-o', 'StrictHostKeyChecking=no', '-P', DVWA_SSH_PORT
    ] + ssh_auth + [
        local_source_backup,
        f'{DVWA_USER}@{DVWA_HOST}:{remote_source_backup}'
    ]

result = subprocess.run(scp_cmd)
if result.returncode != 0:
    print("Failed to upload source backup to remote server.")
    sys.exit(1)

print("Source backup uploaded successfully.")

# Step 4: Upload database backup to remote server
remote_db_backup = f"/tmp/{os.path.basename(local_db_backup)}"
print(f"Uploading database backup to remote server...")

if ssh_auth[0] == 'sshpass':
    scp_cmd = ssh_auth + [
        'scp', '-o', 'StrictHostKeyChecking=no', '-P', DVWA_SSH_PORT,
        local_db_backup,
        f'{DVWA_USER}@{DVWA_HOST}:{remote_db_backup}'
    ]
else:
    scp_cmd = [
        'scp', '-o', 'StrictHostKeyChecking=no', '-P', DVWA_SSH_PORT
    ] + ssh_auth + [
        local_db_backup,
        f'{DVWA_USER}@{DVWA_HOST}:{remote_db_backup}'
    ]

result = subprocess.run(scp_cmd)
if result.returncode != 0:
    print("Failed to upload database backup to remote server.")
    sys.exit(1)

print("Database backup uploaded successfully.")

# Step 5: Extract source backup on remote server
print("Extracting source backup on remote server...")
extract_cmd = f"tar -xvzf {remote_source_backup} -C {DVWA_WEB_PATH}/"

if ssh_auth[0] == 'sshpass':
    ssh_cmd = ssh_auth + [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT,
        f'{DVWA_USER}@{DVWA_HOST}',
        extract_cmd
    ]
else:
    ssh_cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT
    ] + ssh_auth + [
        f'{DVWA_USER}@{DVWA_HOST}',
        extract_cmd
    ]

result = subprocess.run(ssh_cmd)
if result.returncode != 0:
    print("Failed to extract source backup on remote server.")
    sys.exit(1)

print("Source files restored successfully.")

# Step 6: Restore database on remote server
print("Restoring database on remote server...")
restore_db_cmd = f"mysql -u {DVWA_DB_USER} -p'{DVWA_DB_PASSWORD}' {DVWA_DB_NAME} < {remote_db_backup}"

if ssh_auth[0] == 'sshpass':
    ssh_cmd = ssh_auth + [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT,
        f'{DVWA_USER}@{DVWA_HOST}',
        restore_db_cmd
    ]
else:
    ssh_cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT
    ] + ssh_auth + [
        f'{DVWA_USER}@{DVWA_HOST}',
        restore_db_cmd
    ]

result = subprocess.run(ssh_cmd)
if result.returncode != 0:
    print("Failed to restore database on remote server.")
    sys.exit(1)

print("Database restored successfully.")

# Step 7: Clean up temporary files on remote server (optional)
print("Cleaning up temporary files on remote server...")
cleanup_cmd = f"rm -f {remote_source_backup} {remote_db_backup}"

if ssh_auth[0] == 'sshpass':
    ssh_cmd = ssh_auth + [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT,
        f'{DVWA_USER}@{DVWA_HOST}',
        cleanup_cmd
    ]
else:
    ssh_cmd = [
        'ssh', '-o', 'StrictHostKeyChecking=no', '-p', DVWA_SSH_PORT
    ] + ssh_auth + [
        f'{DVWA_USER}@{DVWA_HOST}',
        cleanup_cmd
    ]

subprocess.run(ssh_cmd)  # Don't fail if cleanup fails

print("\nRestore completed successfully!")
print(f"DVWA has been restored to {DVWA_HOST}")
