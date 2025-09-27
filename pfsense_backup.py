import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

PFSENSE_HOST = os.getenv('PFSENSE_HOST')
PFSENSE_USER = os.getenv('PFSENSE_USER')
PFSENSE_PASSWORD = os.getenv('PFSENSE_PASSWORD')
PFSENSE_BACKUP_PATH = os.getenv('PFSENSE_BACKUP_PATH')
LOCAL_BACKUP_DIR = os.getenv('LOCAL_BACKUP_DIR')
GDRIVE_FOLDER_ID = os.getenv('GDRIVE_FOLDER_ID')

# Check required env vars
required_vars = [
    'PFSENSE_HOST', 'PFSENSE_USER', 'PFSENSE_PASSWORD',
    'PFSENSE_BACKUP_PATH', 'LOCAL_BACKUP_DIR', 'GDRIVE_FOLDER_ID'
]
for var in required_vars:
    if not os.getenv(var):
        print(f"Missing required env var: {var}")
        sys.exit(1)

# Ensure local backup directory exists
Path(LOCAL_BACKUP_DIR).mkdir(parents=True, exist_ok=True)

# Generate backup filename
date_str = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file = f"pfsense_backup_{date_str}.xml"
local_backup_path = os.path.join(LOCAL_BACKUP_DIR, backup_file)

# Check for sshpass
if subprocess.call(['which', 'sshpass'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
    print("sshpass is required for password authentication. Please install it (e.g., brew install hudochenkov/sshpass/sshpass).")
    sys.exit(1)

# Download backup from pfSense
print(f"Backing up pfSense config from {PFSENSE_HOST}...")
scp_cmd = [
    'sshpass', '-p', PFSENSE_PASSWORD,
    'scp', '-o', 'StrictHostKeyChecking=no',
    f"{PFSENSE_USER}@{PFSENSE_HOST}:{PFSENSE_BACKUP_PATH}",
    local_backup_path
]
result = subprocess.run(scp_cmd)
if result.returncode != 0:
    print("Failed to download backup from pfSense.")
    sys.exit(1)

print(f"Backup downloaded to {local_backup_path}")

# Upload to Google Drive
gdrive_cmd = [
    'gdrive', 'files', 'upload', '--parent', GDRIVE_FOLDER_ID, local_backup_path
]
print(f"Uploading backup to Google Drive folder {GDRIVE_FOLDER_ID}...")
result = subprocess.run(gdrive_cmd)
if result.returncode == 0:
    print("Backup uploaded to Google Drive successfully.")
else:
    print("Failed to upload backup to Google Drive.")
    sys.exit(1)
