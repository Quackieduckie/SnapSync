#!/usr/bin/env python3
import os
import sys
import subprocess
import json
import getpass
from pathlib import Path

def check_root():
    """Check if script is run with sudo."""
    if os.geteuid() != 0:
        print("This script must be run with sudo privileges.")
        sys.exit(1)

def setup_virtual_env():
    """Set up Python virtual environment and install requirements."""
    print("\n=== Setting up Python virtual environment ===")
    venv_path = os.path.join(os.getcwd(), "epaper-env")
    
    if not os.path.exists(venv_path):
        subprocess.run(["python3", "-m", "venv", venv_path], check=True)
    
    # Install requirements
    pip_path = os.path.join(venv_path, "bin", "pip")
    subprocess.run([pip_path, "install", "Pillow", "psutil"], check=True)
    print("✓ Virtual environment setup complete")

def get_input(prompt, default=None):
    """Get user input with optional default value."""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()

def setup_backup_config():
    """Configure backup sources and paths."""
    print("\n=== Configuring Backup System ===")
    config = {
        'backup_sources': [],
        'bk0_path': '/mnt/bk0',
        'bk1_path': '/mnt/bk1',
        'status_file': '/home/pi/backup_status.txt'
    }
    
    while True:
        print("\nAdd a backup source:")
        source = {
            'name': get_input("Source name (e.g., 'laptop')"),
            'user': get_input("SSH username"),
            'host': get_input("SSH hostname/IP"),
            'port': get_input("SSH port", "22"),
            'path': get_input("Source path to backup")
        }
        config['backup_sources'].append(source)
        
        if input("\nAdd another source? (y/N): ").lower() != 'y':
            break
    
    config['bk0_path'] = get_input("BK0 backup path", config['bk0_path'])
    config['bk1_path'] = get_input("BK1 backup path", config['bk1_path'])
    config['status_file'] = get_input("Status file path", config['status_file'])
    
    # Save config
    with open('backup_config.json', 'w') as f:
        json.dump(config, f, indent=4)
    print("✓ Backup configuration saved")
    return config

def setup_ssh_keys(config):
    """Set up SSH keys for backup sources."""
    print("\n=== Setting up SSH Keys ===")
    home = str(Path.home())
    ssh_dir = os.path.join(home, ".ssh")
    key_path = os.path.join(ssh_dir, "id_ed25519")
    
    if not os.path.exists(ssh_dir):
        os.makedirs(ssh_dir, mode=0o700)
    
    if not os.path.exists(key_path):
        if input("Generate new SSH key? (Y/n): ").lower() != 'n':
            subprocess.run(["ssh-keygen", "-t", "ed25519", "-C", "snapsync", "-f", key_path], check=True)
    
    for source in config['backup_sources']:
        print(f"\nCopy SSH key to {source['host']}?")
        if input("Proceed? (Y/n): ").lower() != 'n':
            try:
                subprocess.run(["ssh-copy-id", "-i", f"{key_path}.pub", 
                              f"{source['user']}@{source['host']}"], check=True)
                print(f"✓ SSH key copied to {source['host']}")
            except subprocess.CalledProcessError:
                print(f"! Failed to copy SSH key to {source['host']}")

def create_systemd_service():
    """Create and enable systemd service."""
    print("\n=== Setting up Systemd Service ===")
    service_path = "/etc/systemd/system/system_stats.service"
    current_dir = os.getcwd()
    
    service_content = f"""[Unit]
Description=E-Paper System Stats
After=network.target

[Service]
User=pi
WorkingDirectory={current_dir}
Environment="PYTHONPATH={current_dir}/e-Paper/RaspberryPi_JetsonNano/python"
ExecStart={current_dir}/epaper-env/bin/python {current_dir}/system_stats_v8.2.py
Restart=always

[Install]
WantedBy=multi-user.target
"""
    
    with open(service_path, 'w') as f:
        f.write(service_content)
    
    subprocess.run(["systemctl", "daemon-reload"], check=True)
    subprocess.run(["systemctl", "enable", "system_stats.service"], check=True)
    subprocess.run(["systemctl", "start", "system_stats.service"], check=True)
    print("✓ Systemd service created and started")

def setup_cron(config):
    """Set up cron job for backups."""
    print("\n=== Setting up Cron Job ===")
    if input("Set up daily backup cron job? (Y/n): ").lower() != 'n':
        backup_time = get_input("Backup time (HH:MM)", "02:00")
        hour, minute = backup_time.split(":")
        
        cron_cmd = f"{minute} {hour} * * * {os.getcwd()}/backup.sh"
        
        # Add to crontab
        current_crontab = subprocess.check_output(["crontab", "-l"]).decode()
        if cron_cmd not in current_crontab:
            with open("/tmp/crontab.tmp", "w") as f:
                f.write(current_crontab + cron_cmd + "\n")
            subprocess.run(["crontab", "/tmp/crontab.tmp"], check=True)
            os.remove("/tmp/crontab.tmp")
            print(f"✓ Cron job set for {backup_time}")

def main():
    """Main setup function."""
    print("=== SnapSync Setup ===")
    check_root()
    
    try:
        setup_virtual_env()
        config = setup_backup_config()
        setup_ssh_keys(config)
        create_systemd_service()
        setup_cron(config)
        
        print("\n=== Setup Complete ===")
        print("You can check the service status with: sudo systemctl status system_stats.service")
        print("View logs with: sudo journalctl -u system_stats.service")
        
    except Exception as e:
        print(f"\nError during setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 