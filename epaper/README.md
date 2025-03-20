# SnapSync E-Paper Display

This repository contains the code for the SnapSync E-Paper display system, which shows system statistics and backup status.

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
- Required Python packages (install in virtual environment):
  - Pillow
  - psutil

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Quackieduckie/SnapSync.git
cd SnapSync/epaper
```

2. Set up Python virtual environment:
```bash
python3 -m venv epaper-env
source epaper-env/bin/activate
pip install Pillow psutil
```

3. Configure systemd service:
```bash
sudo nano /etc/systemd/system/system_stats.service
```

Add the following content:
```ini
[Unit]
Description=E-Paper System Stats
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/SnapSync/epaper
Environment="PYTHONPATH=/home/pi/SnapSync/epaper/e-Paper/RaspberryPi_JetsonNano/python"
ExecStart=/home/pi/SnapSync/epaper/epaper-env/bin/python /home/pi/SnapSync/epaper/system_stats_v8.2.py
Restart=always

[Install]
WantedBy=multi-user.target
```

4. Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable system_stats.service
sudo systemctl start system_stats.service
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

## Service Management

- Check service status: `sudo systemctl status system_stats.service`
- Stop service: `sudo systemctl stop system_stats.service`
- Start service: `sudo systemctl start system_stats.service`
- View logs: `sudo journalctl -u system_stats.service`

## Directory Structure

- `system_stats_v8.2.py`: Main display script
- `fonts/`: Contains required font files
- `e-Paper/`: Waveshare e-Paper display driver (submodule)

## License

MIT License - see LICENSE file for details
