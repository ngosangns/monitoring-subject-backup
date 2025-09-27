import os
import subprocess
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env
load_dotenv()

PFSENSE_HOST = os.getenv('PFSENSE_HOST')
PFSENSE_USER = os.getenv('PFSENSE_USER')
PFSENSE_PASSWORD = os.getenv('PFSENSE_PASSWORD')
PFSENSE_BACKUP_PATH = os.getenv('PFSENSE_BACKUP_PATH')
LOCAL_BACKUP_DIR = os.getenv('LOCAL_BACKUP_DIR')
GDRIVE_FILE_ID = os.getenv('GDRIVE_FILE_ID')  # The Google Drive file ID to restore

# Check required env vars
required_vars = [
    'PFSENSE_HOST', 'PFSENSE_USER', 'PFSENSE_PASSWORD',
    'PFSENSE_BACKUP_PATH', 'LOCAL_BACKUP_DIR', 'GDRIVE_FILE_ID'
]
for var in required_vars:
    if not os.getenv(var):
        print(f"Missing required env var: {var}")
        sys.exit(1)

# Ensure local backup directory exists
Path(LOCAL_BACKUP_DIR).mkdir(parents=True, exist_ok=True)

# Download backup file from Google Drive

# Use --destination for gdrive v3+ (if available)
gdrive_download_cmd = [
    'gdrive', 'files', 'download', '--destination', LOCAL_BACKUP_DIR, '--overwrite', GDRIVE_FILE_ID
]
print(f"Downloading backup file from Google Drive (ID: {GDRIVE_FILE_ID})...")
result = subprocess.run(gdrive_download_cmd)
if result.returncode != 0:
    print("Failed to download backup file from Google Drive.")
    sys.exit(1)

# Find the downloaded file name
def get_downloaded_filename(folder, file_id):
    # gdrive names the file as <file_id> if the original name is not available
    for f in os.listdir(folder):
        if file_id in f:
            return os.path.join(folder, f)
    # fallback: return the most recent file
    files = [os.path.join(folder, f) for f in os.listdir(folder)]
    return max(files, key=os.path.getctime)

local_backup_path = get_downloaded_filename(LOCAL_BACKUP_DIR, GDRIVE_FILE_ID)
print(f"Backup file downloaded to {local_backup_path}")

# Check for sshpass
if subprocess.call(['which', 'sshpass'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
    print("sshpass is required for password authentication. Please install it (e.g., brew install hudochenkov/sshpass/sshpass).")
    sys.exit(1)

# Upload backup to pfSense

# Always upload to a temp path, then move to /cf/conf/config.xml
remote_tmp_path = f"/tmp/restore_config.xml"
print(f"Uploading backup file to pfSense server {PFSENSE_HOST}...")
scp_cmd = [
    'sshpass', '-p', PFSENSE_PASSWORD,
    'scp', '-o', 'StrictHostKeyChecking=no',
    local_backup_path,
    f"{PFSENSE_USER}@{PFSENSE_HOST}:{remote_tmp_path}"
]
result = subprocess.run(scp_cmd)
if result.returncode == 0:
    print("Backup file uploaded to pfSense server successfully.")
else:
    print("Failed to upload backup file to pfSense server.")
    sys.exit(1)

# Restore config and reboot pfSense
print("Restoring config and rebooting pfSense server (overwrite /cf/conf/config.xml)...")
# Move uploaded file to /cf/conf/config.xml and reboot
restore_cmd = f'mv {remote_tmp_path} /cf/conf/config.xml && reboot'
ssh_cmd = [
    'sshpass', '-p', PFSENSE_PASSWORD,
    'ssh', '-o', 'StrictHostKeyChecking=no',
    f'{PFSENSE_USER}@{PFSENSE_HOST}',
    restore_cmd
]
result = subprocess.run(ssh_cmd)
if result.returncode == 0:
    print("Config restored and pfSense is rebooting.")
else:
    print("Failed to restore config or reboot pfSense.")
    sys.exit(1)
