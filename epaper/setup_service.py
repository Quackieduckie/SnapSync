#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

def get_script_path():
    """Get the absolute path of the system_stats script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, "system_stats_v8.2.py")

def check_service_exists():
    """Check if the systemd service already exists."""
    service_name = "snapsync-epaper.service"
    service_path = f"/etc/systemd/system/{service_name}"
    return os.path.exists(service_path)

def create_service_file():
    """Create the systemd service file content."""
    script_path = get_script_path()
    venv_path = os.path.join(os.path.dirname(script_path), "epaper-env")
    python_path = os.path.join(venv_path, "bin", "python")
    
    service_content = f"""[Unit]
Description=SnapSync E-Paper Display Service
After=network.target

[Service]
ExecStart={python_path} {script_path}
WorkingDirectory={os.path.dirname(script_path)}
StandardOutput=inherit
StandardError=inherit
Restart=always
User=root

[Install]
WantedBy=multi-user.target
"""
    return service_content

def prompt_user():
    """Prompt user for service creation."""
    response = input("Would you like to create a systemd service to run the e-Paper display at startup? (y/N): ").lower()
    return response == 'y'

def setup_service():
    """Main function to set up the systemd service."""
    if not os.geteuid() == 0:
        print("This script must be run with sudo privileges.")
        sys.exit(1)

    if check_service_exists():
        print("SnapSync E-Paper service already exists.")
        return

    if not prompt_user():
        print("Service creation cancelled.")
        return

    service_name = "snapsync-epaper.service"
    service_path = f"/etc/systemd/system/{service_name}"
    
    try:
        # Create service file
        service_content = create_service_file()
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        # Set permissions
        os.chmod(service_path, 0o644)
        
        # Reload systemd daemon
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        
        # Enable and start service
        subprocess.run(["systemctl", "enable", service_name], check=True)
        subprocess.run(["systemctl", "start", service_name], check=True)
        
        print(f"Service {service_name} has been created and started successfully!")
        print("\nYou can manage the service with these commands:")
        print(f"  Check status: sudo systemctl status {service_name}")
        print(f"  Stop service: sudo systemctl stop {service_name}")
        print(f"  Start service: sudo systemctl start {service_name}")
        print(f"  View logs: sudo journalctl -u {service_name}")
        
    except Exception as e:
        print(f"Error creating service: {e}")
        if os.path.exists(service_path):
            os.remove(service_path)
        sys.exit(1)

if __name__ == "__main__":
    setup_service() 