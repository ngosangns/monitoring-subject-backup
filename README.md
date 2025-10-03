# Monitoring Subject Backup & Restore Scripts

This project provides Python scripts to back up and restore configurations for **pfSense** and **DVWA** (Damn Vulnerable Web Application), with automated uploads to Google Drive.

## Features

### pfSense Backup & Restore

- **Backup:**
  - Connects to pfSense via SSH (password-based, using sshpass)
  - Downloads the configuration backup file (`/cf/conf/config.xml`)
  - Uploads the backup to a specified Google Drive folder (using the `gdrive` CLI)
- **Restore:**
  - Downloads a backup file from Google Drive
  - Uploads the backup to pfSense via SSH
  - Restores the configuration and reboots pfSense

### DVWA Backup & Restore

- **Backup:**
  - Connects to DVWA server via SSH (supports both SSH key and password authentication)
  - Creates tar.gz archive of web application source code
  - Dumps MySQL database using mysqldump
  - Downloads both backups to local machine
  - Uploads backups to Google Drive
- **Restore:**
  - Downloads source and database backups from Google Drive
  - Uploads backups to DVWA server
  - Extracts source code to `/var/www/html/`
  - Restores MySQL database
  - Cleans up temporary files

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
     # Edit .env with your pfSense and DVWA info
     ```
   - Required variables for **pfSense**:

     - `PFSENSE_HOST`: pfSense IP or hostname
     - `PFSENSE_USER`: pfSense SSH username
     - `PFSENSE_PASSWORD`: pfSense SSH password
     - `PFSENSE_BACKUP_PATH`: Path to pfSense config file (default: `/cf/conf/config.xml`)
     - `LOCAL_BACKUP_DIR`: Local directory to store backups
     - `GDRIVE_FOLDER_ID`: Google Drive folder ID to upload backups
     - `GDRIVE_FILE_ID`: Google Drive file ID to restore (for restore script only)

   - Required variables for **DVWA**:
     - `DVWA_HOST`: DVWA server IP or hostname
     - `DVWA_USER`: SSH username (default: `root`)
     - `DVWA_PASSWORD`: SSH password (optional if using SSH key)
     - `DVWA_SSH_PORT`: SSH port (default: `2222`)
     - `DVWA_SSH_KEY`: Path to SSH private key (optional if using password)
     - `DVWA_WEB_PATH`: Path to web root (default: `/var/www/html`)
     - `DVWA_DB_NAME`: Database name (default: `dvwa`)
     - `DVWA_DB_USER`: Database user (default: `root`)
     - `DVWA_DB_PASSWORD`: MySQL password
     - `LOCAL_BACKUP_DIR`: Local directory to store backups (shared with pfSense)
     - `GDRIVE_FOLDER_ID`: Google Drive folder ID (shared with pfSense)
     - `GDRIVE_SOURCE_FILE_ID`: Google Drive file ID for source backup (for restore only)
     - `GDRIVE_DB_FILE_ID`: Google Drive file ID for database backup (for restore only)

## Usage

### pfSense

#### Backup pfSense Configuration

Run the backup script:

```sh
python pfsense_backup.py
```

- Downloads the pfSense config file and uploads it to your Google Drive folder.
- Check the output for success or error messages.

#### Restore pfSense Configuration

1. Set the `GDRIVE_FILE_ID` environment variable in your `.env` file to the ID of the backup file you want to restore from Google Drive.
2. Run the restore script:

```sh
python pfsense_restore.py
```

- Downloads the specified backup file from Google Drive, uploads it to pfSense, restores the configuration, and reboots pfSense.

### DVWA

#### Backup DVWA Application

Run the backup script:

```sh
python dvwa_backup.py
```

This will:

1. Create a tar.gz archive of DVWA source code on the server
2. Create a MySQL database dump on the server
3. Download both files to your local machine
4. Upload both backups to Google Drive

#### Restore DVWA Application

1. Set the `GDRIVE_SOURCE_FILE_ID` and `GDRIVE_DB_FILE_ID` environment variables in your `.env` file to the IDs of the backup files you want to restore from Google Drive.
2. Run the restore script:

```sh
python dvwa_restore.py
```

This will:

1. Download source and database backups from Google Drive
2. Upload both files to the DVWA server
3. Extract source code to `/var/www/html/`
4. Restore MySQL database
5. Clean up temporary files on the server

## Notes

### General

- Make sure SSH access is enabled on your pfSense device and DVWA server.
- The `gdrive` tool must be authenticated before use (see its documentation).
- All backups are stored locally in `LOCAL_BACKUP_DIR` before being uploaded to Google Drive.

### pfSense

- The restore script will reboot your pfSense device after restoring the configuration.
- Uses `sshpass` for password-based authentication.

### DVWA

- Supports both SSH key-based and password-based authentication.
- SSH key authentication is preferred for better security (set `DVWA_SSH_KEY` path).
- If using password authentication, `sshpass` is required.
- Make sure the MySQL user has permissions to dump and restore the database.
- The restore process will overwrite existing DVWA files and database.

## Project Structure

```
.
├── pfsense_backup.py       # pfSense backup script
├── pfsense_restore.py      # pfSense restore script
├── dvwa_backup.py          # DVWA backup script
├── dvwa_backup.sh          # Legacy DVWA backup bash script
├── dvwa_restore.py         # DVWA restore script
├── dvwa_restore.sh         # Legacy DVWA restore bash script
├── .env                    # Environment configuration (git ignored)
├── .env.example            # Example environment configuration
├── pfsense_backups/        # Local backup storage directory
└── README.md               # This file
```

## License

MIT
