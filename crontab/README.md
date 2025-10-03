# Crontab Setup

This directory contains crontab configuration files for automating daily backups.

## Installation

### Method 1: Manual Installation

1. **Edit root's crontab:**

   ```bash
   sudo crontab -e
   ```

2. **Add the following lines:**

   ```cron
   # Set PATH
   PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin

   # DVWA Backup - runs daily at 2:00 AM
   0 2 * * * cd /opt/monitoring-subject-backup && /usr/bin/python3 dvwa_backup.py >> /var/log/dvwa-backup.log 2>&1

   # pfSense Backup - runs daily at 3:00 AM
   0 3 * * * cd /opt/monitoring-subject-backup && /usr/bin/python3 pfsense_backup.py >> /var/log/pfsense-backup.log 2>&1
   ```

3. **Save and exit** (in vi/vim: press `ESC`, type `:wq`, press `ENTER`)

### Method 2: Install from Template

1. **Copy and edit the template:**

   ```bash
   cp crontab/backup-crontab.example /tmp/backup-crontab
   # Edit /tmp/backup-crontab to match your installation path
   ```

2. **Install the crontab:**

   ```bash
   sudo crontab /tmp/backup-crontab
   ```

3. **Verify installation:**
   ```bash
   sudo crontab -l
   ```

## Cron Schedule Format

```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday is 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

### Examples:

- `0 2 * * *` - Run at 2:00 AM every day
- `0 */6 * * *` - Run every 6 hours
- `0 0 * * 0` - Run at midnight every Sunday
- `30 3 1 * *` - Run at 3:30 AM on the 1st of every month

## Management

### View current crontab:

```bash
sudo crontab -l
```

### Edit crontab:

```bash
sudo crontab -e
```

### Remove crontab:

```bash
sudo crontab -r
```

### View cron logs:

On most Linux systems:

```bash
# View system cron logs
sudo grep CRON /var/log/syslog

# View specific backup logs
tail -f /var/log/dvwa-backup.log
tail -f /var/log/pfsense-backup.log
```

On systems using journalctl:

```bash
sudo journalctl -u cron -f
```

## Troubleshooting

### Cron job is not running:

1. **Check if cron service is running:**

   ```bash
   sudo systemctl status cron    # Debian/Ubuntu
   sudo systemctl status crond   # CentOS/RHEL
   ```

2. **Verify crontab is installed:**

   ```bash
   sudo crontab -l
   ```

3. **Check cron logs:**
   ```bash
   sudo grep CRON /var/log/syslog | tail -20
   ```

### Script errors:

1. **Check backup logs:**

   ```bash
   tail -50 /var/log/dvwa-backup.log
   tail -50 /var/log/pfsense-backup.log
   ```

2. **Test script manually:**

   ```bash
   cd /opt/monitoring-subject-backup
   sudo python3 dvwa_backup.py
   ```

3. **Common issues:**
   - PATH not set correctly (commands like `gdrive`, `sshpass` not found)
   - Working directory not set (can't find `.env` file)
   - Permissions issues (log files not writable)
   - Environment variables not loaded

### PATH issues:

If cron can't find commands, add the full PATH at the top of your crontab:

```cron
PATH=/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin
```

Or use full paths in the cron command:

```cron
0 2 * * * cd /opt/monitoring-subject-backup && /usr/bin/python3 dvwa_backup.py
```

## Advanced Configuration

### Email notifications:

Add `MAILTO` at the top of your crontab to receive email notifications:

```cron
MAILTO=admin@example.com
```

### Custom environment variables:

```cron
PATH=/usr/local/bin:/usr/bin:/bin
BACKUP_DIR=/opt/monitoring-subject-backup

0 2 * * * cd $BACKUP_DIR && /usr/bin/python3 dvwa_backup.py
```

### Redirect output:

- `>> /var/log/backup.log 2>&1` - Append both stdout and stderr to log file
- `> /dev/null 2>&1` - Discard all output (not recommended for debugging)
- `2>&1 | tee -a /var/log/backup.log` - Display and log output

## Cleanup Old Backups

The example crontab includes optional cleanup jobs to remove backups older than 7 days:

```cron
# Clean up backups older than 7 days
0 4 * * * find /opt/monitoring-subject-backup/pfsense_backups -name "*.xml" -mtime +7 -delete
0 4 * * * find /opt/monitoring-subject-backup/pfsense_backups -name "*.tar.gz" -mtime +7 -delete
0 4 * * * find /opt/monitoring-subject-backup/pfsense_backups -name "*.sql" -mtime +7 -delete
```

Adjust `-mtime +7` to change the retention period (e.g., `+30` for 30 days).

## Comparison: Cron vs Systemd Timers

### Use Cron if:

- You prefer traditional Unix tools
- You need simple scheduling
- Your system doesn't use systemd

### Use Systemd Timers if:

- You want better logging integration
- You need dependency management
- You want persistent timers (run missed jobs on boot)
- Your system uses systemd (most modern Linux distros)

See `../systemd/README.md` for systemd timer setup.
