# SnapSync Epaper Display

A system monitoring display for SnapSync backup system using a Waveshare 4.2" e-Paper display.

## Features
- Real-time CPU usage monitoring
- Disk usage monitoring for root and backup drives
- Network traffic monitoring
- CPU temperature monitoring
- Backup status display
- Partial refresh support for faster updates
- Dithering effects for progress bars
- Configurable backup system with multiple source support

## Requirements
- Raspberry Pi (tested on Raspberry Pi 4)
- Waveshare 4.2" e-Paper display (V2)
- Python 3.7+
- Required fonts:
  - DotMatrixTwoExtended.ttf (included)
  - Perfect_DOS_VGA_437.ttf (download required)
- Two backup drives (BK0 and BK1)
- SSH access to backup sources

## Installation
```bash
# Create and activate virtual environment
python3 -m venv epaper-env
source epaper-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download required fonts
mkdir -p fonts
# DotMatrixTwoExtended.ttf is already included
# Download Perfect_DOS_VGA_437.ttf from:
# https://github.com/arcdetri/sample-fonts/raw/master/Perfect%20DOS%20VGA%20437.ttf
# and place it in the fonts directory
```

## Configuration
1. Configure the backup system:
```bash
python configure_backup.py
```
This will guide you through setting up:
- Backup source servers
- Backup paths
- Status file location

2. Set up SSH keys for remote servers:
```bash
ssh-keygen -t ed25519 -C "snapsync"
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@host
```

3. Set up cron job (optional):
```bash
# Edit crontab
crontab -e

# Add line for daily backup (e.g., at 2 AM)
0 2 * * * /path/to/backup.sh
```

## Usage
```bash
# Run the display script
python system_stats_v8.2.py
```

## Display Configuration
- Backup status file path: `/home/pi/backup_status.txt`
- Update interval: 30 seconds
- Partial refresh limit: 20 updates before full refresh

## Notes
- The script requires root access to read CPU temperature
- Make sure the e-Paper display is properly connected to the Raspberry Pi
- The display updates every 30 seconds to minimize wear on the e-Paper display
- Fonts are now loaded from the local `fonts` directory
- BK1 is mounted read-only by default and only remounted rw during backup
- Backup status messages are kept short to fit the display
