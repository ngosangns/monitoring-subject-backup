# pfSense Backup & Restore Scripts

This project provides scripts to back up your pfSense configuration and upload the backup to Google Drive, as well as restore a backup from Google Drive to your pfSense device.

## Features

- **Backup:**
  - Connects to pfSense via SSH (password-based, using sshpass)
  - Downloads the configuration backup file
  - Uploads the backup to a specified Google Drive folder (using the `gdrive` CLI)
- **Restore:**
  - Downloads a backup file from Google Drive
  - Uploads the backup to pfSense via SSH
  - Restores the configuration and reboots pfSense

## Requirements

- Python 3.7+
- `sshpass` (for non-interactive SSH password authentication)
- `gdrive` (Google Drive CLI tool)
- `python-dotenv` (for loading environment variables from `.env`)

## Setup

1. **Clone this repository**
2. **Install dependencies:**
   - Install `sshpass`:
     ```sh
     brew install hudochenkov/sshpass/sshpass  # macOS
     # or use your package manager for Linux
     ```
   - Install `gdrive`:
     - Download and install from https://github.com/prasmussen/gdrive
     - Authenticate with your Google account as per `gdrive` instructions
   - Install Python dependencies:
     ```sh
     pip install python-dotenv
     ```
3. **Configure environment variables:**
   - Copy `.env.example` to `.env` and fill in your details:
     ```sh
     cp .env.example .env
     # Edit .env with your pfSense and Google Drive info
     ```
   - Required variables:

- `PFSENSE_HOST`: pfSense IP or hostname
- `PFSENSE_USER`: pfSense SSH username
- `PFSENSE_PASSWORD`: pfSense SSH password
- `PFSENSE_BACKUP_PATH`: Path to pfSense config file (default: `/cf/conf/config.xml`)
- `LOCAL_BACKUP_DIR`: Local directory to store backups
- `GDRIVE_FOLDER_ID`: Google Drive folder ID to upload backups (for backup script)
- `GDRIVE_FILE_ID`: Google Drive file ID to restore (for restore script)

## Usage

### Backup pfSense Configuration

Run the backup script:

```sh
python pfsense_backup.py
```

- Downloads the pfSense config file and uploads it to your Google Drive folder.
- Check the output for success or error messages.

### Restore pfSense Configuration

1. Set the `GDRIVE_FILE_ID` environment variable in your `.env` file to the ID of the backup file you want to restore from Google Drive.
2. Run the restore script:

```sh
python pfsense_restore.py
```

- Downloads the specified backup file from Google Drive, uploads it to pfSense, restores the configuration, and reboots pfSense.

## Notes

- Make sure SSH access is enabled on your pfSense device.
- The scripts use `sshpass` for password-based authentication. For better security, consider using SSH keys (manual modification required).
- The `gdrive` tool must be authenticated before use (see its documentation).
- The restore script will reboot your pfSense device after restoring the configuration.

## License

MIT
