# Systemd Service & Timer Setup

This directory contains systemd service and timer files to automate daily backups for DVWA and pfSense.

## Files

- `dvwa-backup.service` - Service definition for DVWA backup
- `dvwa-backup.timer` - Timer to run DVWA backup daily at 2:00 AM
- `pfsense-backup.service` - Service definition for pfSense backup
- `pfsense-backup.timer` - Timer to run pfSense backup daily at 3:00 AM

## Installation

1. **Copy the project to the target location:**

   ```bash
   sudo mkdir -p /opt/monitoring-subject-backup
   sudo cp -r /path/to/your/project/* /opt/monitoring-subject-backup/
   sudo chmod +x /opt/monitoring-subject-backup/*.py
   ```

2. **Copy systemd files to systemd directory:**

   ```bash
   sudo cp systemd/*.service /etc/systemd/system/
   sudo cp systemd/*.timer /etc/systemd/system/
   ```

3. **Set proper permissions:**

   ```bash
   sudo chmod 644 /etc/systemd/system/dvwa-backup.service
   sudo chmod 644 /etc/systemd/system/dvwa-backup.timer
   sudo chmod 644 /etc/systemd/system/pfsense-backup.service
   sudo chmod 644 /etc/systemd/system/pfsense-backup.timer
   ```

4. **Reload systemd daemon:**

   ```bash
   sudo systemctl daemon-reload
   ```

5. **Enable and start the timers:**

   ```bash
   # Enable DVWA backup timer
   sudo systemctl enable dvwa-backup.timer
   sudo systemctl start dvwa-backup.timer

   # Enable pfSense backup timer
   sudo systemctl enable pfsense-backup.timer
   sudo systemctl start pfsense-backup.timer
   ```

## Configuration

### Customize Backup Times

Edit the timer files to change when backups run:

- **DVWA backup:** Default is 2:00 AM daily
- **pfSense backup:** Default is 3:00 AM daily

To change the time, edit the `OnCalendar` line in the respective timer file:

```ini
OnCalendar=*-*-* HH:MM:SS
```

For example, to run at 1:30 AM:

```ini
OnCalendar=*-*-* 01:30:00
```

After making changes, reload the systemd daemon and restart the timer:

```bash
sudo systemctl daemon-reload
sudo systemctl restart dvwa-backup.timer
```

### Customize Working Directory

If you install the project in a different location than `/opt/monitoring-subject-backup`, update the following in the service files:

1. `WorkingDirectory` - Path to the project directory
2. `ExecStart` - Full path to the Python script

## Management Commands

### Check timer status:

```bash
# List all timers
sudo systemctl list-timers

# Check specific timer status
sudo systemctl status dvwa-backup.timer
sudo systemctl status pfsense-backup.timer
```

### Check service status:

```bash
sudo systemctl status dvwa-backup.service
sudo systemctl status pfsense-backup.service
```

### View service logs:

```bash
# View recent logs
sudo journalctl -u dvwa-backup.service -n 50
sudo journalctl -u pfsense-backup.service -n 50

# Follow logs in real-time
sudo journalctl -u dvwa-backup.service -f
sudo journalctl -u pfsense-backup.service -f

# View logs for a specific date
sudo journalctl -u dvwa-backup.service --since "2025-10-03"
```

### Manually trigger a backup:

```bash
# Run DVWA backup manually
sudo systemctl start dvwa-backup.service

# Run pfSense backup manually
sudo systemctl start pfsense-backup.service
```

### Stop/disable timers:

```bash
# Stop timers
sudo systemctl stop dvwa-backup.timer
sudo systemctl stop pfsense-backup.timer

# Disable timers (prevent auto-start on boot)
sudo systemctl disable dvwa-backup.timer
sudo systemctl disable pfsense-backup.timer
```

## Troubleshooting

### Timer is not running:

1. Check if timer is enabled and active:

   ```bash
   sudo systemctl is-enabled dvwa-backup.timer
   sudo systemctl is-active dvwa-backup.timer
   ```

2. Check timer logs:
   ```bash
   sudo journalctl -u dvwa-backup.timer
   ```

### Service fails:

1. Check service status:

   ```bash
   sudo systemctl status dvwa-backup.service
   ```

2. View detailed logs:

   ```bash
   sudo journalctl -u dvwa-backup.service -n 100
   ```

3. Test the script manually:

   ```bash
   cd /opt/monitoring-subject-backup
   sudo python3 dvwa_backup.py
   ```

4. Verify:
   - `.env` file exists and has correct permissions
   - All required dependencies are installed
   - Network connectivity to target hosts
   - SSH credentials are correct
   - Google Drive authentication is configured

## Alternative: Using Crontab

If you prefer using traditional cron instead of systemd timers:

1. **Edit root's crontab:**

   ```bash
   sudo crontab -e
   ```

2. **Add the following lines:**

   ```cron
   # DVWA Backup - runs daily at 2:00 AM
   0 2 * * * cd /opt/monitoring-subject-backup && /usr/bin/python3 dvwa_backup.py >> /var/log/dvwa-backup.log 2>&1

   # pfSense Backup - runs daily at 3:00 AM
   0 3 * * * cd /opt/monitoring-subject-backup && /usr/bin/python3 pfsense_backup.py >> /var/log/pfsense-backup.log 2>&1
   ```

3. **View cron logs:**
   ```bash
   tail -f /var/log/dvwa-backup.log
   tail -f /var/log/pfsense-backup.log
   ```

## Notes

- Services run as `root` user to ensure proper permissions for SSH and file operations
- `Persistent=true` ensures that if the system is off during the scheduled time, the backup will run when the system starts
- Logs are stored in systemd journal and can be viewed with `journalctl`
- The timers are staggered (DVWA at 2 AM, pfSense at 3 AM) to avoid resource contention
