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
- Required fonts (included in repository):
  - DotMatrixTwoExtended.ttf
  - Perfect_DOS_VGA_437.ttf
- Two backup drives (BK0 and BK1)
- SSH access to backup sources

## Quick Installation

1. Clone the repository:
```bash
git clone https://github.com/Quackieduckie/SnapSync.git
cd SnapSync/epaper
```

2. Run the setup script:
```bash
sudo ./setup.py
```

The setup script will:
- Set up Python virtual environment with required packages
- Configure backup sources and paths
- Set up SSH keys for remote backup
- Create and enable the systemd service
- Optionally set up a daily backup cron job

## Manual Installation
If you prefer to set up components manually, follow these steps:

1. Set up Python virtual environment:
```bash
python3 -m venv epaper-env
source epaper-env/bin/activate
pip install Pillow psutil
```

2. Configure backup sources:
```bash
python configure_backup.py
```

3. Set up SSH keys:
```bash
ssh-keygen -t ed25519 -C "snapsync"
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@host
```

4. Create systemd service:
```bash
sudo nano /etc/systemd/system/system_stats.service
```

Add the following content (adjust paths as needed):
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

5. Enable and start service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable system_stats.service
sudo systemctl start system_stats.service
```

## Service Management

- Check service status: `sudo systemctl status system_stats.service`
- Stop service: `sudo systemctl stop system_stats.service`
- Start service: `sudo systemctl start system_stats.service`
- View logs: `sudo journalctl -u system_stats.service`

## Backup Configuration

The backup configuration is stored in `backup_config.json` with the following structure:
```json
{
    "backup_sources": [
        {
            "name": "laptop",
            "user": "username",
            "host": "192.168.1.100",
            "port": "22",
            "path": "/path/to/backup"
        }
    ],
    "bk0_path": "/mnt/bk0",
    "bk1_path": "/mnt/bk1",
    "status_file": "/home/pi/backup_status.txt"
}
```

## Directory Structure

- `system_stats_v8.2.py`: Main display script
- `setup.py`: Installation and configuration script
- `configure_backup.py`: Backup configuration utility
- `fonts/`: Contains required font files
- `e-Paper/`: Waveshare e-Paper display driver (submodule)
- `backup_config.json`: Backup configuration file
- `backup.sh`: Generated backup script

## License

MIT License - see LICENSE file for details
